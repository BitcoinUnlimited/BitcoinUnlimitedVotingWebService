from sqlalchemy import LargeBinary, Integer, Float, String, Column, ForeignKey, Boolean, PickleType

from sqlalchemy.orm import relationship
import sqlalchemy.orm.exc
from butype import *
from trawfile import RawFile
from taction import Action
from tmemberlist import MemberList
from tproposalmetadata import ProposalMetadata
from jvalidate import ValidationError

class ProposalVote(db.Model, BUType):
    """ Vote on a proposal. """
    __tablename__ = "proposal_vote"
    
    id = Column(Integer, primary_key=True)
    x_json = Column(LargeBinary, nullable=False)
    x_sha256 = Column(String(length=64), nullable=False, unique=True)

    raw_file_id = Column(Integer, ForeignKey("raw_file.id"), nullable=False, unique=True)
    raw_file = relationship(RawFile, uselist = False)

    proposal_metadata_id = Column(Integer, ForeignKey("proposal_metadata.id"),
                                  nullable=False, unique=True)
    proposal_metadata = relationship(ProposalMetadata, uselist=False,
                                     back_populates="vote")
    
    # _creating_ action for proposal vote (opening vote)
    action_id = Column(Integer, ForeignKey("action.id"), nullable=False, unique=True)
    action = relationship("Action", uselist=False)

    method_name = Column(String, nullable=False)
    
    method_options = Column(PickleType, nullable=False)

    result = relationship("ProposalVoteResult", uselist=False)
    
    def __init__(self,
                 raw_file,
                 proposal_metadata,
                 action, 
                 method_name,
                 method_options):
        if proposal_metadata.vote is not None:
            raise ValidationError("Vote on proposal(metadata) that "+
                                  "has already a vote attached.")
        
        self.raw_file = raw_file
        self.proposal_metadata = proposal_metadata
        self.action = action
        self.method_name = method_name
        self.method_options = method_options
        self.xUpdate()

    @classmethod
    def by_raw_file_hash(cls, href):
        """ Returns proposal vote by raw file hash reference. """
        raw_file = RawFile.by_hash(href)

        if raw_file is None:
            return None
        
        try:
            return cls.query.filter(cls.raw_file == raw_file).one()
        except sqlalchemy.orm.exc.NoResultFound:
            return None
        
    def toJ(self):
        return defaultExtend(self, {
            "file_hash" : self.raw_file.hashref(),
            "meta" : self.proposal_metadata.toJ(),
            "action" : self.action.toJ(),
            "method_name" : self.method_name,
            "method_options" : self.method_options
            })

    def dependencies(self):
        return [self.raw_file, self.proposal_metadata,
                self.action]
