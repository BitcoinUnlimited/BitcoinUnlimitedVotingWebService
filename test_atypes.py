import pytest
from jvalidate import ValidationError
from atypes import *
from jvalidate import ValidationError
from butype import *
from butypes import *
from test_helpers import *


def test_tSHA256():
    assert tSHA256("0"*64) == "0" * 64
    with pytest.raises(ValidationError):
        tSHA256("1"*63)

    with pytest.raises(ValidationError):
        tSHA256("2"*65)

def test_tInt():
    assert tInt("12345") == 12345
    with pytest.raises(ValidationError):
        tInt("abc")
        
def test_tMemberName():
    assert tMemberName("test") == "test"
    with pytest.raises(ValidationError):
        tMemberName("X"*80)

    with pytest.raises(ValidationError):
        tMemberName("X"*20+"\x00")
        
def test_tTokenList():
    assert tTokenList({}, [1,2,3]) == [1,2,3]
    with pytest.raises(ValidationError):
        tTokenList({}, "")
    
def test_tAddress():
    with pytest.raises(ValidationError):
        tAddress("X"*100)
    with pytest.raises(ValidationError):
        tAddress("X"*20)

    vaddr = makeTestKey("test")[1]
    return tAddress(vaddr) == vaddr

def test_tSafeString():
    assert tSafeString("'"+"X"*100+"'") == "X" * 100
    assert tSafeString('"'+"X"*100+'"') == "X" * 100
    with pytest.raises(ValidationError):
        tSafeString("X"*100)

    with pytest.raises(ValidationError):
        tSafeString('"'+"X"*100)

    with pytest.raises(ValidationError):
        tSafeString("'"+"X"*100)
        
    with pytest.raises(ValidationError):
        tSafeString("\x00")

    with pytest.raises(ValidationError):
        tSafeString("'\x00'")
        
def test_tYesNo():
    assert tYesNo("yes")
    assert not tYesNo("no") 
    with pytest.raises(ValidationError):
        tYesNo("YES")

    with pytest.raises(ValidationError):
        tYesNo("any")

def test_tAccRejAbs():
    assert tAccRejAbs("accept") == "accept"
    assert tAccRejAbs("reject") == "reject"
    with pytest.raises(ValidationError):
        tAccRejAbs("YES")

    with pytest.raises(ValidationError):
        tAccRejAbs("any")
        
def test_tCurrentMember(bare_session, member_a):
    assert tCurrentMember("member_a") == "member_a"

    with pytest.raises(ValidationError):
        assert tCurrentMember("member_nonexist")

def test_tVoteMaster(bare_session, member_a, member_v):
    assert tVoteMaster("member_v") == "member_v"

    with pytest.raises(ValidationError):
        assert tVoteMaster("member_a")

def test_tVoteMethod():
    assert tVoteMethod({}, ["buip-acc-rej-abs"]) == ("buip-acc-rej-abs", {})
    
    with pytest.raises(ValidationError):
        assert tVoteMethod({}, ["invalid"])

def test_tVoteAnswer(bare_session, proposal_vote):
    context={"vote_hash" : proposal_vote.hashref()}
    assert tVoteAnswer(context, ["accept"]) == ("buip-acc-rej-abs", {"answer" : "accept"})

    # no vote_hash
    invalid_context1={}
    with pytest.raises(ValidationError):
        tVoteAnswer(invalid_context1, ["accept"])

    # vote_hash invalid
    invalid_context2={"vote_hash" : "0"*64}
    with pytest.raises(ValidationError):
        tVoteAnswer(invalid_context2, ["accept"])

    # vote method wrong
    proposal_vote.method_name="invalid"
    with pytest.raises(ValidationError):
        tVoteAnswer(context, ["accept"])
        
         
def test_tMemberAccRejAbs():
    assert tMemberAccRejAbs("accept") == ("member-vote-acc-rej-abs", {"answer" : "accept"})
    assert tMemberAccRejAbs("reject") == ("member-vote-acc-rej-abs", {"answer" : "reject"})
    assert tMemberAccRejAbs("abstain") == ("member-vote-acc-rej-abs", {"answer" : "abstain"})
