import pytest
import tmember
from butype import *
import butypes
import tproposalmetadata
from test_tmemberlist import makeTestMemberList, makeTestKey
from jvalidate import ValidationError


def test_invalid_construction1():
    name, addr = "fakemember", makeTestKey("fakemember")[1]
    member = tmember.Member(name, addr)

    assert not butypes.is_used(member)
    
    with pytest.raises(ValidationError):
        rf = member
        md = tproposalmetadata.ProposalMetadata("test.pdf",
                                                "application/pdf",
                                                rf, None)
        
