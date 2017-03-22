from butypes import *
import pytest
import bitcoin
import config
from taction import Action
from test_tmemberlist import makeTestMemberList
from jvalidate import ValidationError
from test_taction import makeTestAction
from test_helpers import DummyUpload, bare_session
from trawfile import RawFile

zero256="0000000000000000000000000000000000000000000000000000000000000000"
emptyhash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        

def test1(bare_session):
    ml = makeTestMemberList(None)
    ml.set_current()
    
    inv1=makeTestAction(author=Member.by_name("member_a"),
                     apart =
                     (ml.hashref()+" proposal-upload file %s by member_b" % emptyhash))

    val1=makeTestAction(author=Member.by_name("member_a"),
                        apart =
                        (ml.hashref()+" proposal-upload file %s by member_a" % emptyhash))

    inv2=makeTestAction(author=Member.by_name("member_a"),
                        apart =
                        (ml.hashref()+" proposal-upload file %s by member_a" % zero256))
    
    
    upload = DummyUpload("testfile.txt", "text/plain")

    with pytest.raises(ValidationError):
        inv1.apply(upload, b"")

    with pytest.raises(ValidationError):
        inv2.apply(upload, b"")
        
    val1.apply(upload, b"")
    
