import pytest
import bitcoin
from jvalidate import ValidationError
from tmember import Member
from tmemberlist import *
from test_helpers import bare_session
from butype import db
from test_helpers import makeTestKey, makeTestMemberKeys, makeTestMemberList

def test1(bare_session):
    ml = makeTestMemberList(None)

    assert len(ml.members) == 26

    for m in ml.members:
        assert m.member_lists == [ml]

    non_existent_member=Member("nonexistmember",
                               makeTestKey("nonexist")[1])

    with pytest.raises(ValidationError):
        MemberList(
            members = ml.members,
            secretary = non_existent_member,
            president = ml.president,
            developer = ml.developer)

    with pytest.raises(ValidationError):
        MemberList(
            members = ml.members,
            secretary = ml.secretary,
            president = non_existent_member,
            developer = ml.developer)

    with pytest.raises(ValidationError):
        MemberList(
            members = ml.members,
            secretary = ml.secretary,
            president = ml.president,
            developer = non_existent_member)

        
def test2(bare_session):
    ml = makeTestMemberList(None)
    assert not ml.current()

    ml.set_current()
    assert ml.current()
    
def test3(bare_session):
    ml = makeTestMemberList(None)

    assert len(ml.members) == 26

    duplicate_member=Member("member_a",
                               makeTestKey("test1")[1])
    
    with pytest.raises(ValidationError):
        MemberList(
            members = ml.members+[duplicate_member],
            secretary = ml.secretary,
            president = ml.president,
            developer = ml.developer)
