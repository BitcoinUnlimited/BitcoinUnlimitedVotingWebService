#!/usr/bin/env python3
# Create dummy test environment
import os
import logging
logging.basicConfig(level=logging.DEBUG)

from sqlalchemy import func
from sqlalchemy.orm import aliased

import config
import hashlib
from butypes import *
from butype import *
from test_tmemberlist import makeTestMemberList
from test_helpers import DummyUpload
from test_taction import makeTestAction
from appmaker import make_app
from test_scenarios import *

app, db = make_app()
