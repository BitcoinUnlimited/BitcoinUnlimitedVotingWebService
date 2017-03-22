#!/usr/bin/env python3
# Create dummy test environment
import os
import logging
logging.basicConfig(level=logging.DEBUG)
import config
import hashlib

import sys
from butypes import *
from butype import *
from test_tmemberlist import makeTestMemberList
from test_helpers import DummyUpload
from test_taction import makeTestAction
from appmaker import make_app
from test_scenarios import *

if len(sys.argv) < 2:
    print("Please specify stop point or empty string.")
    exit(1)
    
app, db = make_app(fresh=True)
test_scenario1(db.session, sys.argv[1])

db.session.commit()
