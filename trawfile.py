import hashlib
from sqlalchemy import LargeBinary, Integer, Float, ForeignKey, Column, String
from sqlalchemy.orm import relationship
from jvalidate import ValidationError
from butype import *



class RawFile(db.Model, BUType):
    """ An uploaded (raw) file, for example the PDF of a BUIP. """
    
    __tablename__="raw_file"

    id = Column(Integer, primary_key=True)
    x_sha256 = Column(String(length=64), nullable=False, unique=True)
    data = Column(LargeBinary, nullable=False)

    # metadata that refers to this file 
    proposal_metadata = relationship("ProposalMetadata",
                                     uselist=False,
                                     back_populates = "raw_file")
    
    def __init__(self, data=None):
        self.data=data
        dhash=hashlib.sha256(data).hexdigest()
        orf=RawFile.by_hash(dhash)
        if orf is not None:
            raise ValidationError("Raw file with hash '%s' exists already." % dhash)
            
        self.xUpdate()
        
    def public(self):
        return (self.proposal_metadata is not None and
                self.proposal_metadata.file_public)
    
    def serialize(self):
        return bytes(self.data)

    def hashref(self):
        return sha256(self.serialize())
    
    def toJ(self):
        raise RuntimeError("Cannot create JSON representation of raw file.")

    def xUpdate(self):
        self.x_sha256=self.hashref()
        
    def dependencies(self):
        return []
