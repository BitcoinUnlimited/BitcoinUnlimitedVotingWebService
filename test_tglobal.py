import time
import pytest
import config
import urlvalidate
import hashlib
from butype import *
from butypes import *
from test_helpers import bare_session


def test_vmr(bare_session):
    assert Global.get_votemaster_roles() == []

    Global.set_votemaster_rules(["a", "b", "president"])

    assert Global.get_votemaster_roles() == ["a", "b", "president"]
    
