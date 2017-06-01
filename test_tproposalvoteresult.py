import pytest
import tmember
from butype import *
from butypes import *
from tproposalvote import ProposalVote
from tproposalvoteresult import ProposalVoteResult
from test_tmemberlist import makeTestMemberList, makeTestKey
from jvalidate import ValidationError
from test_helpers import raw_file, proposal_vote, proposal_vote_result, proposal_vote_ballot, bare_session, makeTestAction



def test_invalid_construction1():
    with pytest.raises(ValidationError):
        ProposalVoteResult(None)

    
def test_invalid_construction2(bare_session, proposal_vote):
    with pytest.raises(ValidationError):
        # vote has already result attached
        ProposalVoteResult(proposal_vote)

def test_invalid_vote_twice(bare_session, proposal_vote_result):
    pvr = proposal_vote_result
    proposal_vote_result.cast(proposal_vote_ballot(pvr), "buip-acc-rej-abs", "accept")

    with pytest.raises(ValidationError):
        proposal_vote_result.cast(proposal_vote_ballot(pvr), "buip-acc-rej-abs", "accept")

def test_invalid_vote_closed(bare_session, proposal_vote_result):
    pvr = proposal_vote_result
    pvr.close()
    with pytest.raises(ValidationError):
        proposal_vote_result.cast(proposal_vote_ballot(pvr), "buip-acc-rej-abs", "accept")

def test_invalid_vote_old(bare_session, proposal_vote_result):
    return # disabled, see 276ee5935eedbded9a474957a2e0e3db649e40bc for reason
    pvr = proposal_vote_result
    newml = makeTestMemberList(Global.current_member_list())
    Global.set_current_member_list(newml)
    pvb=proposal_vote_ballot(pvr)
    with pytest.raises(ValidationError):
        proposal_vote_result.cast(pvb, "buip-acc-rej-abs", "accept")


def test_invalid_method(bare_session, proposal_vote_result):
    pvr = proposal_vote_result
    pvb=proposal_vote_ballot(pvr)
    with pytest.raises(ValidationError):
        proposal_vote_result.cast(pvb, "non-existing", "accept")


def test_invalid_non_eligible(bare_session, proposal_vote_result):
    pvr = proposal_vote_result
    config.member_expiry_time = 0.0
    with pytest.raises(ValidationError):
        proposal_vote_result.cast(proposal_vote_ballot(pvr), "buip-acc-rej-abs", "accept")
    config.member_expiry_time = 86400 * 365
    
