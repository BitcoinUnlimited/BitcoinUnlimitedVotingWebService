import os
import pytest
import bitcoin
import config
from taction import Action
from tmultiaction import MultiAction
from butypes import Global
from test_tmemberlist import makeTestMemberList
from jvalidate import ValidationError
from test_helpers import bare_session, member_list, member_a, newmember5

zero256="0000000000000000000000000000000000000000000000000000000000000000"

from test_helpers import makeTestAction, member_a

def mas1(member_list):
    multi_action_string1 = (
        config.action_prefix + member_list.hashref() +" delete-objects [] by member_v"+
        "\n@@@@@\n" +
        config.action_prefix + member_list.hashref() + " delete-objects [] by member_v"+
        "\n@@@@@\n" +
        config.action_prefix + member_list.hashref() + " delete-objects [] by member_v")
    return multi_action_string1

def test_construct1(bare_session, member_list, member_a):

    privkey = bitcoin.sha256(member_a.name)

    multi_action_string = mas1(member_list)
    multi_signature  = bitcoin.ecdsa_sign(
        multi_action_string, privkey)
    
    ma = MultiAction(member_a, 
                     multi_action_string,
                     multi_signature)
    
    assert len(ma.actions) == 3

def test_invalid1(bare_session, member_list, member_a):
    privkey = bitcoin.sha256("invalid")

    multi_action_string = mas1(member_list)

    multi_signature  = bitcoin.ecdsa_sign(multi_action_string, privkey)

    with pytest.raises(ValidationError):
        ma = MultiAction(member_a, 
                         multi_action_string,
                         multi_signature)
