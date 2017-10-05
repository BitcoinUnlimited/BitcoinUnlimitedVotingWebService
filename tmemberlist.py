import bitcoin 
from sqlalchemy import LargeBinary, Integer, Float, String, Column, ForeignKey, Boolean, Table
from sqlalchemy.orm import relationship
import re
import jvalidate
from jvalidate import ValidationError
from butype import *
from tglobal import Global
from tmember_assoc import members_in_memberlists

class MemberList(db.Model, BUType):
    """ A list of members. If the member list is current, it is *the* member list to be used
    for all BU voting. """
    __tablename__="member_list"

    id = Column(Integer, primary_key = True)
    x_json = Column(LargeBinary, nullable=False)
    x_sha256 = Column(String(length=64), nullable=False)

    members = relationship("Member", secondary = members_in_memberlists,
                           back_populates="member_lists")

    secretary_id = Column(Integer, ForeignKey("member.id"), nullable=False)
    secretary = relationship("Member", uselist=False, foreign_keys=secretary_id)
    president_id = Column(Integer, ForeignKey("member.id"), nullable=False)
    president = relationship("Member", uselist=False, foreign_keys=president_id)
    developer_id = Column(Integer, ForeignKey("member.id"), nullable=False)
    developer = relationship("Member", uselist=False, foreign_keys=developer_id)

    previous_id = Column(Integer, ForeignKey("member_list.id"), unique=True)
    previous = relationship("MemberList", uselist=False, foreign_keys=previous_id)
    
    def __init__(self,
                 members,
                 secretary,
                 president,
                 developer,
                 previous=None):

        mnames = set(m.name for m in members)
        if len(mnames)<len(members):
            raise ValidationError("Duplicate members in list.")
        
        self.members = members
        self.secretary = secretary
        self.president = president
        self.developer = developer

        if secretary not in self.members:
            raise ValidationError("Secretary not listed as member.")

        if president not in self.members:
            raise ValidationError("President not listed as member.")

        if developer not in self.members:
            raise ValidationError("Developer not listed as member.")

        self.previous=previous
        
        self.xUpdate()
        
    def toJ(self):
        return defaultExtend(self, {
            "members" : sorted([m.toJ() for m in self.members],
                               key = lambda m : m["name"]),
            "secretary" : self.secretary.toJ(),
            "president" : self.president.toJ(),
            "developer" : self.developer.toJ(),
            "previous" : self.previous.hashref() if self.previous else None
        })

    def dependencies(self):
        r=list(self.members)
        if self.previous is not None:
            r.append(self.previous)
        return r
        
    def current(self):
        """ Returns true if this is the current member list. """
        return Global.current_member_list() == self

    def set_current(self):
        Global.set("current_member_list", self.id)


    def extraRender(self):
        r = super().extraRender()
        r["current"]=self.current()
        r["proposals"]=self.proposals()
        return r

    def proposals(self):
        from taction import Action
        from tproposalmetadata import ProposalMetadata
        return (ProposalMetadata
                        .query
                        .join(ProposalMetadata.action)
                        .filter(Action.member_list == self))
        
    def applications(self):
        from taction import Action
        from tmemberelectionresult import MemberElectionResult
        return (MemberElectionResult
                        .query
                        .join(MemberElectionResult.action)
                        .filter(Action.member_list == self))


