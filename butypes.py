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


def get_all_objects(): # for debugging & testing
    res = {}
    for Cls in types:
        for obj in Cls.query:
            res[obj.x_sha256]=obj
    return res

