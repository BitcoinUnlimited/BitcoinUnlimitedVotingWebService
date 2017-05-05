import sqlalchemy.orm.exc
from sqlalchemy import LargeBinary, Integer, Float, String, Column, ForeignKey, Boolean, Table
from sqlalchemy.orm import relationship
from butype import *

class Global(db.Model):
    """ Global state stored as (key, value) string pairs in the DB,
plus some convenience methods on top.
    """
    
    id = Column(Integer, primary_key=True)
    key = Column(String, nullable=False, unique=True)
    value = Column(String, nullable=False)

    @classmethod
    def get(cls, k):
        """ Return value for key. """
        objs = cls.query.filter(cls.key == k).all()
        assert len(objs)<2
        if not len(objs):
            raise KeyError("'%s' not found." % k)
        else:
            return objs[0].value
        
    @classmethod
    def set(cls, k, v):
        """ Set value for key. Overrides old value if it exists. """
        x=cls.query.filter(cls.key == k).all()
        if len(x):
            x[0].value = v
        else:
            db.session.add(cls(key = k, value = v))

    @classmethod
    def current_member_list(cls):
        """ Return the current member list. """
        from tmemberlist import MemberList
        try:
            cml_id=int(cls.get("current_member_list"))
        except KeyError:
            return None
        return MemberList.query.get(cml_id)

            
    @classmethod
    def set_current_member_list(cls, ml):
        """ Set the current member list. """
        cls.set("current_member_list", ml.id)
        
    @classmethod
    def member_last_vote_time(cls, member):
        try:
            return float(cls.get("member_last_vote_time_"+member.name))
        except:
            return None

    @classmethod
    def set_member_last_vote_time(cls, member, time):
        cls.set("member_last_vote_time_"+member.name,
                str(time))
 

    @classmethod
    def get_votemaster_roles(cls):
        """ Return a list of strings describing the official roles that
        have votemaster rights. """
        try:
            return cls.get("votemaster_roles").split()
        except KeyError:
            return []

    @classmethod
    def set_votemaster_rules(cls, vmr):
        """ Set the members having votemaster role. """
        cls.set("votemaster_roles", " ".join(vmr))
        
