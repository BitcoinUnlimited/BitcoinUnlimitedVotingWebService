import os
import pytest
import bitcoin
import config
from taction import Action
from butypes import Global
from test_tmemberlist import makeTestMemberList
from jvalidate import ValidationError
from test_helpers import bare_session, member_list, member_a, newmember5

zero256="0000000000000000000000000000000000000000000000000000000000000000"

from test_helpers import makeTestAction, member_a

def test1(bare_session):
    ml = makeTestMemberList(None)
    
    ml.set_current()
    
    # only formatting of action is tested, not content
    a = makeTestAction(author=ml.members[0],
                       apart =
                       (ml.hashref()+" proposal-upload file  %s by member_b" % zero256))


def test_invalid(bare_session, member_list, member_a, newmember5):
    # invalid signature string (not base64)
    with pytest.raises(ValidationError):
        Action(member_a, "123", "invalidsig\x00")
    
    # valid signature, but wrong address
    action_string = "123"
    privkey = bitcoin.sha256("invalid")
    signature = bitcoin.ecdsa_sign(action_string, privkey)

    with pytest.raises(ValidationError):
        Action(member_a, action_string, signature)


    # invalid action string (no prefix)
    action_string = "invalid"
    privkey = bitcoin.sha256(member_a.name)
    signature = bitcoin.ecdsa_sign(action_string, privkey)
        
    with pytest.raises(ValidationError):
        Action(member_a, action_string, signature)

    # invalid action string (no member list)
    action_string = config.action_prefix+(64*"0")
    privkey = bitcoin.sha256(member_a.name)
    signature = bitcoin.ecdsa_sign(action_string, privkey)
        
    with pytest.raises(ValidationError):
        Action(member_a, action_string, signature)


    # invalid action string (member not in current list)
    action_string = config.action_prefix+member_list.hashref()
    privkey = bitcoin.sha256(newmember5.name)
    signature = bitcoin.ecdsa_sign(action_string, privkey)
        
    with pytest.raises(ValidationError):
        Action(newmember5, action_string, signature)



        
def test_invalid_newml(bare_session, member_list, member_a):
    newml = makeTestMemberList(Global.current_member_list())
    Global.set_current_member_list(newml)
        
    # invalid action string (not current member list)
    action_string = config.action_prefix+member_list.hashref()
    privkey = bitcoin.sha256(member_a.name)
    signature = bitcoin.ecdsa_sign(action_string, privkey)
        
    with pytest.raises(ValidationError):
        Action(member_a, action_string, signature)
        

        
                       
        
    
        
