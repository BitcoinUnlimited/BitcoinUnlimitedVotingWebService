import time
import pytest
import bitcoin
import testkeys
import config
from jvalidate import ValidationError
from tmember import Member
from tglobal import Global
from test_helpers import bare_session, member_list, member_a, member_list_no_vote_times
import sqlalchemy.exc


def test1(bare_session):
    m=Member(name="member_a",
           address="19L8fQDCta3mewpJXcRm8wqq5X6k6HFign")
    bare_session.add(m)
    bare_session.commit()

    assert not m.eligible()
    Global.set_member_last_vote_time(m, time.time())

    # member is still not eligible - because no
    # current member list exists
    assert not m.eligible()
    
    
    assert not len(m.dependencies())
    
    assert len(m.member_lists) == 0
    
    with pytest.raises(ValidationError):
        Member(name="member_a ", # illegal name
               address="19L8fQDCta3mewpJXcRm8wqq5X6k6HFign")

    with pytest.raises(ValidationError):
        Member(name="member_a",
               # Bitcoin address with broken checksum
               address="19L8fQDCta3mewpJXcRm8wqq6X6k6HFign")

    m2=Member(name="member_b",
              address="1FPZ29pzqC1FLYyDuB5Han6wi8oNwQeHCV")
    bare_session.add(m2)
    bare_session.commit()
    
    # not allowed: reuse of address
    with pytest.raises(ValidationError):
        m3=Member(name="member_a",
                  address="1FPZ29pzqC1FLYyDuB5Han6wi8oNwQeHCV")

def test_duplicate_name(bare_session):
    m1=Member(name="member_a",
              address="19L8fQDCta3mewpJXcRm8wqq5X6k6HFign")

    bare_session.add(m1)
    bare_session.commit()

    with pytest.raises(ValidationError):
        m2=Member(name="member_a",
                  address="1FPZ29pzqC1FLYyDuB5Han6wi8oNwQeHCV")



def test_eligibility(bare_session, member_list, member_a):
    assert member_a.eligible()
    config.member_expiry_time = 0
    assert not member_a.eligible()
    config.member_expiry_time = 86400 * 365

def test_eligibility2(bare_session, member_list_no_vote_times, member_a):
    assert Global.member_last_vote_time(member_a) is None
    assert not member_a.eligible()
    
    
def test_with_pgpkey(bare_session):
    with pytest.raises(ValidationError):
        m=Member(name="member_a",
                 address="19L8fQDCta3mewpJXcRm8wqq5X6k6HFign",
                 pgp_pubkey = "test")

    m=Member(name="member_a",
             address="19L8fQDCta3mewpJXcRm8wqq5X6k6HFign",
             pgp_pubkey = testkeys.pubkey1)
        
    bare_session.add(m)
    bare_session.commit()

    
    
