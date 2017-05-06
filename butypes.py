import os
import logging
import time
import json
import config
import hashlib

import jvalidate
import butypes

log=logging.getLogger(__name__)

from trawfile import RawFile
from taction import Action
from tmember import Member
from tmemberlist import MemberList, members_in_memberlists
from tproposalmetadata import ProposalMetadata
from tproposalvote import ProposalVote
from tproposalvoteresult import ProposalVoteResult
from tmemberelectionresult import MemberElectionResult
from tglobal import Global

types=[RawFile, Action, Member, MemberList, ProposalMetadata,
       ProposalVote, ProposalVoteResult, MemberElectionResult]

name2type=dict((x.__tablename__,x) for x in types)


def get_all_objects():
    """ For debugging and testing - and for the current
    implementation of delete functionality. """
    res = {}
    for Cls in types:
        for obj in Cls.query:
            res[obj.x_sha256]=obj
    return res

def users_of(obj):
    """ Return all objects that are directly referencing 'obj'. """
    # FIXME: this is highly inefficient - but should suffice
    # in the meantime.
    used = []
    all_objs = get_all_objects().values()
    for o in all_objs:
        if obj in o.dependencies():
           used.append(o)
    return used
    
def is_used(obj):
    """ Return true iff obj is used by something else. """
    return len(used_by(obj))
