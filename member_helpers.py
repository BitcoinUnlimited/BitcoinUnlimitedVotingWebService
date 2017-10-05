from butype import *
from butypes import *

def updateMemberinCurrentMemberList(name,
                                    address,
                                    pgp_pubkey = None):
    ml = Global.current_member_list()

    for proposal in ml.proposals():
        if proposal.vote and proposal.vote.is_open:
            raise ValidationError("Current member list has proposal openm for voting.")

    if len(list(ml.applications())):
        raise ValidationError("Current member list has new members applying.")
            
        
    member = Member.by_name(name)
    if member is None:
        raise ValidationError("No recent member '%s' exists." % name)
    
    if member not in ml.members:
        raise ValidationError("Member '%s' not in current member list." % member)

    assert member.most_recent

    member.most_recent = False
    db.session.commit()

    updated_member = Member(name = name,
                            address = member.address if address=="unchanged" else address,
                            pgp_pubkey = member.pgp_pubkey if pgp_pubkey=="unchanged" else pgp_pubkey)

    new_memberlist = ml.members.copy()
    new_memberlist.remove(member)
    new_memberlist.append(updated_member)
    
    new_president = (updated_member
                     if updated_member.name == ml.president.name
                     else ml.president)
    new_secretary = (updated_member
                     if updated_member.name == ml.secretary.name
                     else ml.secretary)
    new_developer = (updated_member
                     if updated_member.name == ml.developer.name
                     else ml.developer)

    new_memberlist=MemberList(
        members = new_memberlist,
        secretary = ml.secretary,
        president = ml.president,
        developer = ml.developer,
        previous = ml)
    db.session.add(updated_member)
    db.session.add(new_memberlist)

    # carry over vote eligibility info into global eligibility table,
    # if that data is available
    lva = member.last_vote_action()
    lmc = member.last_member_confirmation()
    t_elig = max(lva, lmc)
    if t_elig > 0.0:
        Global.set_member_last_vote_time(updated_member, t_elig)

    db.session.commit()
    Global.set_current_member_list(new_memberlist)
