#!/usr/bin/env python3
# Create dummy test environment
import os
import logging
logging.basicConfig(level=logging.DEBUG)
import hashlib
import sqlalchemy.exc
import pytest
import config
import hashlib
from butypes import *
from butype import *
from test_helpers import bare_session
from jvalidate import ValidationError

def test_rawfile1(bare_session):
    rf=RawFile(b"123")
    bare_session.add(rf)
    bare_session.commit()

    assert not rf.public()
    assert rf.serialize() == b"123"

    H=hashlib.sha256(b"123").hexdigest()
    
    assert rf.hashref() == H
    
    with pytest.raises(ValidationError):
        rf2 = RawFile(b"123")

    with pytest.raises(Exception):
        rf.toJ()

    assert not len(rf.dependencies())
