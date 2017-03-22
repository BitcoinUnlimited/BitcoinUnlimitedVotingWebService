import logging
log=logging.getLogger(__name__)

from sqlalchemy import LargeBinary, Integer, Float, String, Column, \
    ForeignKey, Boolean, PickleType, Table

from sqlalchemy.orm import relationship, reconstructor

from jvalidate import ValidationError
from butype import *
from taction import Action
from tproposalvote import ProposalVote

# Map ballots <-> proposal vote results results
ballots_in_results = Table("proposal_vote_ballot_assoc", db.metadata,
                           Column("result_id", Integer, ForeignKey("proposal_vote_result.id")),
                           Column("ballot_id", Integer, ForeignKey("action.id")))


class ProposalVoteResult(db.Model, BUType):
    """ Partial and ongoing or final result of a vote. """
    __tablename__ = "proposal_vote_result"

    id = Column(Integer, primary_key=True)
    x_json = Column(LargeBinary, nullable=False)
    x_sha256 = Column(String(length=64), nullable=False, unique=True)

    is_open = Column(Boolean, nullable=False)
    
    vote_id = Column(Integer, ForeignKey("proposal_vote.id"), nullable=False, unique=True)
    vote = relationship(ProposalVote, uselist = False,
                        back_populates="result")

    ballots = relationship(Action, secondary = ballots_in_results)
                    
    def __init__(self,
                 vote):
        if vote is None:
            raise ValidationError("Vote needed.")
        
        if vote.result is not None: 
            raise ValidationError("Vote already has a result attached.")

        self.vote = vote
        self.is_open = True

        self.reconstruct()
        
        self.xUpdate()

    @reconstructor
    def reconstruct(self):
        from vote_methods import vote_methods
        self.vm = vote_methods[self.vote.method_name]()
        
    def toJ(self):
        return defaultExtend(self, {
            "vote_hash" : self.vote.hashref(),
            "open" : self.is_open,
            "ballots" : sorted(
                [b.toJ() for b in self.ballots],
                key = lambda j : j["author"]["name"])
            })

    def dependencies(self):
        return [self.vote]+self.ballots
    
    def extraRender(self):
        r=super().extraRender()
        r["summary"]=self.summarize()
        return r

    def cast(self, ballot, method_name, answer):
        log.debug("Casting vote: %s, %s, %s", ballot, method_name, answer)
        vote = self.vote
        
        members_voted=set(b.author for b in self.ballots)

        if not self.is_open:
            raise ValidationError("Vote is not open anymore.")
        
        if ballot.member_list != vote.action.member_list:
            raise ValidationError("Cannot vote on old proposal with different member list.")
        
        if ballot.author in members_voted:
            raise ValidationError("Member '%s' voted already." % ballot.author.name)

        if method_name != vote.method_name:
            # should not happen - tVoteAnswer(..) should always set it correctly
            raise ValidationError("Wrong method '%s' expected '%s'." %
                                  (method_name, vote.method_name))

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
        
