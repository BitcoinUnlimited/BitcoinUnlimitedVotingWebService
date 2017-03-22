import pytest
import tmember
from butype import *
from butypes import *
from tmemberelectionresult import MemberElectionResult
from test_tmemberlist import makeTestMemberList, makeTestKey
from jvalidate import ValidationError
from test_helpers import raw_file, proposal_vote, proposal_vote_result, proposal_vote_ballot, bare_session, makeTestAction, member_a, member_list, member_election_result, propose_member_action, member_ballot


def test_invalid_constructions(bare_session, member_list, member_a, propose_member_action):
    assert member_a.eligible()
    with pytest.raises(ValidationError):
          MemberElectionResult(member_a,
                                  propose_member_action)
          

def test_invalid_cast(bare_session, member_list, member_a, member_election_result):
    assert member_a.eligible()
    mer = member_election_result
    with pytest.raises(ValidationError):
        mer.cast(member_ballot(), "non-existing-action", "")

def test_invalid_closed(bare_session, member_list, member_a, member_election_result):
    assert member_a.eligible()
    mer = member_election_result
    mer.close()
    with pytest.raises(ValidationError):
        mer.cast(member_ballot(), "member-vote-acc-rej-abs", "")

def test_invalid_old(bare_session, member_list, member_a, member_election_result):
    assert member_a.eligible()
    mer = member_election_result

    newml = makeTestMemberList(Global.current_member_list())
    Global.set_current_member_list(newml)
    
    with pytest.raises(ValidationError):
        mer.cast(member_ballot(), "member-vote-acc-rej-abs", "")
        

def test_invalid_vote_twice(bare_session, member_list, member_a, member_election_result):
    assert member_a.eligible()
    mer = member_election_result
    mer.cast(member_ballot(), "member-vote-acc-rej-abs", "")
    with pytest.raises(ValidationError):
        mer.cast(member_ballot(), "member-vote-acc-rej-abs", "")


def test_invalid_non_eligible(bare_session, member_list, member_a, member_election_result):
    assert member_a.eligible()
    mer = member_election_result
    config.member_expiry_time = 0.0
    with pytest.raises(ValidationError):
        mer.cast(member_ballot(), "member-vote-acc-rej-abs", "")
    config.member_expiry_time = 86400 * 365
    
        
          
