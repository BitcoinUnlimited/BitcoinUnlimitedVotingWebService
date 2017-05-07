import pytest
import tmember
from butype import *
from butypes import *
from tproposalvote import ProposalVote
from tproposalvoteresult import ProposalVoteResult
from test_tmemberlist import makeTestMemberList, makeTestKey
from jvalidate import ValidationError
from test_helpers import raw_file, proposal_vote, proposal_vote_result, proposal_vote_ballot, bare_session, makeTestAction, member_a, member_list


def test_invalid_already(bare_session, proposal_vote, member_list):
    pv = proposal_vote

    assert len(pv.dependencies()) == 4
    md = pv.proposal_metadata
    rf = md.raw_file
    ml = member_list
    
    with pytest.raises(ValidationError):
        ProposalVote(rf, md, makeTestAction(member_a(),
                                            "%s open-proposal-vote meta %s by member_v method (buip-acc-rej-abs)" % (ml.hashref(), md.hashref())) , "buip-acc-rej-abs", [])


def test_no_result_dep(bare_session, proposal_vote):
    proposal_vote.result=None
    
    assert len(proposal_vote.dependencies()) == 3
  

def test_notexist_raw_file_hash(bare_session, raw_file):
    assert ProposalVote.by_raw_file_hash("0"*64) is None
    assert ProposalVote.by_raw_file_hash(raw_file.hashref()) is None
