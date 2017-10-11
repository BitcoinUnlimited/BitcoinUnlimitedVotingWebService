import pytest
import gnupg
import bitcoin
import testkeys
from jvalidate import ValidationError
from test_helpers import makeTestKey, bare_session
from tmember import Member
from sigver import checkSig, checkSigBitcoin, checkSigGPG
import gpglayer

def test_invalid1():
    with pytest.raises(ValidationError):
        checkSig("invalid message",
                 "invalid signature",
                 "invalid author")


@pytest.fixture(scope="function")
def gpg_env1():
    gpg = gpglayer.gpgInstance() 
    env = {}

    env["gpg"] = gpg

    ki1 = gpg.gen_key_input(passphrase = "key1")
    ki2 = gpg.gen_key_input(passphrase = "key2")

    key1 = gpg.gen_key(ki1)
    key2 = gpg.gen_key(ki2)

    env["key1"] = key1
    env["key2"] = key2
    env["pk1"] = gpg.export_keys(key1.fingerprint)
    env["pk2"] = gpg.export_keys(key2.fingerprint)

    msg1 = b"Message one"
    msg2 = b"Message two"
    env["msg1"] = msg1
    env["msg2"] = msg2

    sig1 = gpg.sign(msg1, keyid = key1.fingerprint,
                    detach = True, passphrase="123")
    env["sig1"] = sig1

    sig2 = gpg.sign(msg2, keyid = key2.fingerprint,
                    detach = True, passphrase="123")
    env["sig2"] = sig2

    yield env

def test_sig_bitcoin1(bare_session):
    msg = "this is a test message"

    name1, name2 = "member_a", "member_b"
    
    priv1, addr1 = makeTestKey(name1)
    priv2, addr2 = makeTestKey(name2)
    
    msg = b"this is a test message"
    sig1 = bitcoin.ecdsa_sign(msg, priv1)
    sig2 = bitcoin.ecdsa_sign(msg, priv2)

    with pytest.raises(ValidationError):
        # member not existing
        checkSig(msg, sig1, name1)

    m1 = Member(name1, addr1)
    m2 = Member(name2, addr2)
    bare_session.add(m1)
    bare_session.add(m2)

    # should succeed
    checkSig(msg, sig1, name1)

    with pytest.raises(ValidationError):
        # wrong sig
        checkSig(msg, sig2, name1)

    # should succeed
    checkSig(msg, sig2, name2)
    
def test_sig_pgp1(gpg_env1, bare_session):
    env = gpg_env1
    gpg = env["gpg"]
    
    name1, name2 = "member_a", "member_b"
    
    priv1, addr1 = makeTestKey(name1)
    priv2, addr2 = makeTestKey(name2)

    m1 = Member(name1, addr1, env["pk1"])
    m2 = Member(name2, addr2, env["pk2"])
    bare_session.add(m1)
    bare_session.add(m2)

    msg = b"this is a test message"

    
    s1 = gpg.sign(msg, keyid = env["key1"].fingerprint,
                    passphrase="key1", detach=True)
    sig1 = s1.data
    
    s2 = gpg.sign(msg, keyid = env["key2"].fingerprint,
                  passphrase="key2", detach=True)
    sig2 = s2.data
    

    # signing should have succeeded (non-zero sig length)
    assert len(sig1) and b"SIGNATURE" in sig1
    assert len(sig2) and b"SIGNATURE" in sig1
    
    # should suceed
    checkSig(msg, sig1, name1)
    checkSig(msg, sig2, name2)
    
    with pytest.raises(ValidationError):
        # wrong user
        checkSig(msg, sig2, name1)
        
        

    
