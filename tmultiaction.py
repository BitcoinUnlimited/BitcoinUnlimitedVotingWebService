from sqlalchemy import LargeBinary, Integer, Float, String, Column, ForeignKey, Boolean
from sqlalchemy.orm import relationship, reconstructor
from butype import *
from tmemberlist import MemberList
from taction import Action
import jvalidate
import sigver
import config


class MultiAction(db.Model, BUType):
    """A signed action. A vote ballot is a special kind of signed
    action.
    """
    __tablename__="multi_action"

    id = Column(Integer, primary_key=True)
    x_json = Column(LargeBinary, nullable=False)
    x_sha256 = Column(String(length=64), nullable=False, unique=True)    

    author_id = Column(Integer, ForeignKey("member.id"), nullable=False)
    author = relationship("Member", uselist=False)
    
    actions = relationship("Action")

    # the concatenated individual actions
    multi_action_string = Column(String, nullable=False)
                       
    multi_signature = Column(String, nullable=False)

    def __init__(self,
                 author,
                 multi_action_string,
                 multi_signature):

        self.author = author
        self.multi_action_string = multi_action_string
        self.multi_signature = multi_signature

        sigver.checkSig(multi_action_string, multi_signature, author.name)

        naction = 0
        for action_string in (multi_action_string
                              .replace("\r", "")
                              .split("\n@@@@@\n")):
            print("At section of multi-action:", repr(action_string))
            # action adds itself to this multi_action
            Action(author, action_string, None, self)
            naction+=1

        if naction == 0:
            raise jvalidate.ValidationError("Multi action needs at least one action.")
        self.xUpdate()

    def toJ(self):
        return defaultExtend(self, {
            "author" : self.author.toJ(),
            "multi_action_string" : self.multi_action_string,
            "multi_signature" : self.multi_signature,
        })

    def dependencies(self):
        return [self.author,
                self.actions]
 
    def apply(self):
        return [action.parser.apply(None, None)
                for action in self.actions]
