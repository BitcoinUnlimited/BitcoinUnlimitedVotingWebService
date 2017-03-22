from sqlalchemy import LargeBinary, Integer, Float, String, Column, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from butype import *
from trawfile import RawFile
from taction import Action
from tmemberlist import MemberList


class ProposalMetadata(db.Model, BUType):
    """ Metadata for a Proposal. Original file name, Proposal date,
    pointer to proposed file and the action used to propose it. """
    __tablename__="proposal_metadata"


    id = Column(Integer, primary_key=True)
    x_json = Column(LargeBinary, nullable=False)
    x_sha256 = Column(String(length=64), nullable=False, unique=True)

    filename = Column(String, nullable=False)
    mime_type = Column(String, nullable=False)

    # _creating_ action
    action_id = Column(Integer, ForeignKey("action.id"), nullable=False)
    action = relationship("Action", uselist=False)
    
    raw_file_id = Column(Integer, ForeignKey("raw_file.id"), nullable=False)
    raw_file = relationship(RawFile,
                            uselist = False,
                            back_populates = "proposal_metadata")

    vote = relationship("ProposalVote", uselist=False)
    
    file_public = Column(Boolean, nullable=False)
    
    def __init__(self,
                 filename,
                 mime_type,
                 raw_file,
                 action,
                 file_public=False):
        self.filename=filename
        self.mime_type=mime_type
        if raw_file.__tablename__ != RawFile.__tablename__:
            raise jvalidate.ValidationError("Needs raw file.")
        
        self.raw_file =raw_file
        self.action =action 
        self.file_public = file_public
        self.member_list = action.member_list
        self.xUpdate()
        
    def toJ(self):
        return defaultExtend(self, {
            "filename" : self.filename,
            "mime_type" : self.mime_type,
            "file_hash" : self.raw_file.hashref(),
            "action" : self.action.toJ(),
            "file_public" : self.file_public
        })

    def dependencies(self):
        return [self.raw_file, self.action]
    
    def extraRender(self):
        r=super().extraRender()
        r.update({"action" : self.action})
        return r
    
    
