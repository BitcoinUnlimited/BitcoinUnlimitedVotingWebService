from butype import *
from butypes import *
from jvalidate import ValidationError
import logging
log=logging.getLogger(__name__)

def addMember(name,
              address,
              pgp_pubkey,
              number,
              last_vote_time):
    ml = Global.current_member_list()

    if len(list(ml.applications())):
        raise ValidationError("Current member list has new members applying.")

    if name in [m.name for m in ml.members]:
        raise ValidationError("Member '%s' exists in current member list." % name)

    member = Member.by_name(name)
    if member is not None:
        raise ValidationError("Recent member '%s' exists." % name)

    new_member = Member(name = name,
                        address = address,
                        pgp_pubkey = pgp_pubkey,
                        number = number)
    hmember = Member.by_hash(new_member.hashref())
    if hmember is not None:
        # FIXME: maybe implement pointing to old member definition here
        log.info("Use existing member with same info.")
        new_member = hmember

    new_memberlist = ml.members.copy()
    new_memberlist.append(new_member)

    new_memberlist=MemberList(
        members = new_memberlist,
        secretary = ml.secretary,
        president = ml.president,
        developer = ml.developer,
        previous = ml)

    if hmember is None:
        db.session.add(new_member)
    db.session.add(new_memberlist)
    db.session.flush() # need to flush so that Global.set* works below

    Global.set_member_last_vote_time(new_member, last_vote_time)
    Global.set_current_member_list(new_memberlist)

def updateMemberinCurrentMemberList(name,
                                    address,
                                    pgp_pubkey = None,
                                    number = None):
    ml = Global.current_member_list()

    # for proposal in ml.proposals():
    #     if (proposal.vote is not None and
    #         proposal.vote.result is not None and
    #         proposal.vote.result.is_open):
    #         raise ValidationError("Current member list has proposal open for voting (%s)." % (proposal.designation))

    if len(list(ml.applications())):
        raise ValidationError("Current member list has new members applying.")


    member = Member.by_name(name)
    if member is None:
        raise ValidationError("No recent member '%s' exists." % name)

    if member not in ml.members:
        raise ValidationError("Member '%s' not in current member list." % member)

    assert member.most_recent

    lva = member.last_vote_action()
    lmc = member.last_member_confirmation()

    member.most_recent = False

    updated_member = Member(name = name,
                            address = member.address if address=="unchanged" else address,
                            pgp_pubkey = member.pgp_pubkey if pgp_pubkey=="unchanged" else pgp_pubkey,
                            number = member.number if number=="unchanged" else number)
    if Member.by_hash(updated_member.hashref()):
        # FIXME: maybe implement pointing to old member definition here
        raise ValidationError("Member exists already.")

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
        secretary = new_secretary,
        president = new_president,
        developer = new_developer,
        previous = ml)
    db.session.add(member)
    db.session.add(updated_member)
    db.session.add(new_memberlist)
    db.session.flush() # need to flush so that Global.set* works below

    # carry over vote eligibility info into global eligibility table,
    # if that data is available
    t_elig = max(lva, lmc)
    if t_elig > 0.0:
        Global.set_member_last_vote_time(member, t_elig)

    Global.set_current_member_list(new_memberlist)


def update_member_cmd(args):
    """ Update a member's info (by creating a new member and updating the member list) """
    import dbenv
    pgp_key = None
    if args.pgp_key_file is not None:
        pgp_key = open(args.pgp_key_file).read()

    updateMemberinCurrentMemberList(
        args.name,
        args.address if args.address is not None else "unchanged",
        pgp_key if pgp_key is not None else "unchanged",
        args.number if args.number is not None else "unchanged")
    db.session.commit()

def add_member_cmd(args):
    """ Add a regular member and update the current member list """
    import time
    import dbenv
    pgp_key = None
    if args.pgp_key_file is not None:
        pgp_key = open(args.pgp_key_file).read()

    last_vote_time = int(time.mktime(time.strptime(args.last_vote_time, "%d-%m-%Y")))

    addMember(
        args.name,
        args.address,
        pgp_key,
        args.number,
        last_vote_time)
    db.session.commit()

def set_member_last_vote_time(args):
    import time
    import dbenv

    member = Member.by_name(args.name)
    if member is None:
        raise ValidationError("No recent member '%s' exists." % args.name)

    Global.set_member_last_vote_time(member, time.mktime(time.strptime(args.last_vote_time, "%d-%m-%Y")))
    db.session.commit()
