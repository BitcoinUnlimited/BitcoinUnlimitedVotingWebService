from sqlalchemy import LargeBinary, Integer, Float, String, Column, ForeignKey, Boolean, PickleType, Table
from sqlalchemy.orm import relationship, reconstructor
import sqlalchemy.orm.exc
from butype import *
from taction import Action
from tmember import Member
from tmemberlist import MemberList
from jvalidate import ValidationError

ballots_map = Table("member_ballot_assoc", db.metadata,
                    Column("result_id", Integer, ForeignKey("member_election_result.id")),
                    Column("ballot_id", Integer, ForeignKey("action.id")))

# FIXME: factor out commonalities with ProposalVote(Result)

class MemberElectionResult(db.Model, BUType):
    """ Result of electing a single member into BU. """
    __tablename__ = "member_election_result"

    id = Column(Integer, primary_key=True)
    x_json = Column(LargeBinary, nullable=False)
    x_sha256 = Column(String(length=64), nullable=False, unique=True)

    new_member_id = Column(Integer, ForeignKey("member.id"), unique=True)
    new_member = relationship(Member, uselist=False)

    # _creating_ action for the new member election
    action_id = Column(Integer, ForeignKey("action.id"), nullable=False, unique=True)
    action = relationship("Action", uselist=False)

    is_open = Column(Boolean, nullable=False)

    ballots = relationship(Action, secondary = ballots_map)

    # number of members eligible to vote when vote is opened
    Nmemb_eligible_opened = Column(Integer, nullable=False)
    
    def __init__(self,
                 new_member,
                 action):

        # FIXME: might be too stringent (re-joining members etc.?) review
        if len(new_member.member_lists):
            # should have been tested in actionexec already
            raise ValidationError("Member is already member of a member list.")

        self.new_member = new_member
        self.action = action

        with db.session.no_autoflush:
            self.Nmemb_eligible_opened = sum(
                member.eligible() for member in action.member_list.members)

        
        self.is_open=True
        self.reconstruct()
        self.xUpdate()

    @reconstructor
    def reconstruct(self):
        from vote_methods import vote_methods
        self.method_name="member-vote-acc-rej-abs"
        self.method_options={}
        self.vm = vote_methods[self.method_name]()

    def toJ(self):
        return defaultExtend(self, {
            "new_member" : self.new_member.toJ(),
            "action" : self.action.toJ(),
            "ballots" : sorted([b.toJ() for b in self.ballots],
                               key = lambda j : j["author"]["name"]),
            "method_name" : self.method_name,
            "method_options" : self.method_options,
            "Nmemb_eligible_opened" : self.Nmemb_eligible_opened,
            "open" : self.is_open
            })

    def dependencies(self):
        return [self.action, self.new_member]+self.ballots


    def extraRender(self):
        r=super().extraRender()
        r["summary"]=self.summarize()
        return r

    @classmethod
    def by_member(cls, member):
        try:
            return (MemberElectionResult.query
                    .filter(MemberElectionResult.new_member == member)).one()
        except sqlalchemy.orm.exc.NoResultFound:
            return None

    def cast(self, ballot, method_name, answer):
        log.debug("Casting new member vote: %s, %s, %s", ballot, method_name, answer)
        members_voted=set(b.author for b in self.ballots)

        if method_name != self.method_name: 
            # should not happen - tVoteAnswer(..) should always set it correctly
            raise ValidationError("Wrong method '%s' expected '%s'." %
                                  (method_name, self.method_name))

        if not self.is_open:
            raise ValidationError("Vote is not open anymore.")

        if ballot.member_list != self.action.member_list: 
            # should not happen as votes need to be closed to create new member lists
            raise ValidationError("Cannot vote on old proposal with different member list.")

        if ballot.author in members_voted:
            raise ValidationError("Member '%s' voted already." % ballot.author.name)

        if not ballot.author.eligible():
            raise ValidationError("Member is not eligible to vote (anymore).")

        self.ballots.append(ballot)
        log.debug("Current ballot list: %s", self.ballots)
        self.xUpdate()

    def summarize(self):
        """ Summarized final or preliminary result. """
        return self.vm.summarize(self)

    def close(self):
        self.is_open = False
        self.xUpdate()

