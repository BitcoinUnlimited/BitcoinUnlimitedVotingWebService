import time
import pytest
import config
import urlvalidate
import hashlib
from butype import *
from butypes import *
from test_highlevel import *
from test_helpers import small_app as app

def test_nonexist(app, client):
    vote_for_raw_file_hash(client, "0"*64)


def test1(app, client):
    for i in range(26):
        member = "member_"+chr(ord('a')+i)
        assert Member.by_name(member).eligible()


    prop1 = b"A test proposal"
    upload_proposal(client,
                    prop1, "test1.txt",
                    "member_a")

    # fail: same twice
    with pytest.raises(UnexpectedStatus):
        upload_proposal(client,
                        prop1, "test1.txt",
                        "member_a")

    assert not is_public_raw_file_hash(client, sha256(prop1))

    # fail: wrong member to publish proposal
    with pytest.raises(UnexpectedStatus):
        publish_proposal(client, prop1, "BUIPxxxx", "proposal title", "member_c")

    assert get_designation(client, sha256(prop1)) == "test1.txt"

    publish_proposal(client, prop1, "BUIP0001", "another proposal title", "member_v")
    assert is_public_raw_file_hash(client, sha256(prop1))

    assert get_designation(client, sha256(prop1)) == "BUIP0001"
    assert get_title(client, sha256(prop1)) == "another proposal title"

    # can't open invalid vote
    with pytest.raises(UnexpectedStatus):
        open_proposal_vote(client, b"doesn't exist", "member_v", "buip-acc-rej-abs")

    open_proposal_vote(client, prop1, "member_v", "buip-acc-rej-abs")

    # can't open vote twice
    with pytest.raises(UnexpectedStatus):
        open_proposal_vote(client, prop1, "member_v", "buip-acc-rej-abs")

    for i in range(26):
        member = "member_"+chr(ord('a')+i)
        answer = ["accept", "reject"][i<15]
        cast_proposal_ballot(client, prop1, member, answer)

    for i in range(26):
        member = "member_"+chr(ord('a')+i)
        assert Member.by_name(member).eligible()

    config.member_expiry_time = 0.25
    time.sleep(0.5)
    for i in range(26):
        member = "member_"+chr(ord('a')+i)
        assert not Member.by_name(member).eligible()
    config.member_expiry_time = 86400 * 365

    propose_member(client, "member_v", "anewmember1")
    assert not Member.by_name("anewmember1").eligible()
    for i in range(26):
        member = "member_"+chr(ord('a')+i)
        answer = ["accept", "reject"][i<5]
        cast_member_ballot(client, member, "anewmember1", answer)

    for i in range(26):
        member = "member_"+chr(ord('a')+i)
        assert Member.by_name(member).eligible()

    # new member not yet in current list
    assert not Member.by_name("anewmember1").eligible()
    close_member_elections(client, "member_v", ["anewmember1"])

    # but now it is
    assert Member.by_name("anewmember1").eligible()

    close_proposal_vote(client, prop1, "member_v")

    assert summary_for_proposal_vote_result(
        client, proposal_result_for_vote_hash(client, vote_for_raw_file_hash(client, sha256(prop1)))) == {
            "quorum_reached" : True, "rejects" : 15, "accepted" : False, "accepts" : 11, "abstains" : 0, "spoiled" : 0 }


def test_vote_more_detail1(app, client):
    prop1 = b"A test proposal"
    upload_proposal(client,
                    prop1, "test1.txt",
                    "member_a")

    publish_proposal(client, prop1, "BUIP0001", "BUIP0001 title", "member_v")
    open_proposal_vote(client, prop1, "member_v", "buip-acc-rej-abs")

    def voteset1(i):
        if i<5:
            answer = "spoil"
        elif i<11:
            answer = "reject"
        elif i<18:
            answer = "accept"
        else:
            answer = "abstain"
        return answer

    for i in range(26):
        member = "member_"+chr(ord('a')+i)
        answer = voteset1(i)
        cast_proposal_ballot(client, prop1, member, answer)

    close_proposal_vote(client, prop1, "member_v")
    assert summary_for_proposal_vote_result(
        client, proposal_result_for_vote_hash(client, vote_for_raw_file_hash(client, sha256(prop1)))) == {
            "quorum_reached" : True,
            "spoiled" : 5,
            "rejects" : 6,
            "accepts" : 7,
            "abstains" : 8,
            "accepted" : True }

    propose_member(client, "member_v", "anewmember1")

    for i in range(26):
        member = "member_"+chr(ord('a')+i)
        answer = voteset1(i)
        cast_member_ballot(client, member, "anewmember1", answer)
    close_member_elections(client, "member_v", ["anewmember1"])

    # FIXME: implement better way to iterate through / access member elections
    me_hashes = all_hashrefs_of_type(client, "member_election_result")
    assert len(me_hashes) == 1
    me_hash = me_hashes[0]

    assert summary_for_member_election_result(
        client, me_hash) == {
            "quorum_reached" : True,
            "spoiled" : 5,
            "rejects" : 6,
            "accepts" : 7,
            "abstains" : 8,
            "accepted" : True }

def test_deletion(app, client):
    prop1 = b"A test proposal"
    upload_proposal(client,
                    prop1, "test1.txt",
                    "member_a")

    publish_proposal(client, prop1, "BUIP0001", "BUIP0001 title", "member_v")

    prop1hash = sha256(prop1)

    meta1hash = meta_for_raw_file_hash(client, prop1hash)

    # delete nonexistent should not work
    with pytest.raises(UnexpectedStatus):
        delete_objects(client, "member_v", [64*"1"])

    # delete current member list should not work
    with pytest.raises(UnexpectedStatus):
        delete_objects(client, "member_v", [Global.current_member_list().hashref()])

    # delete incomplete should not work
    with pytest.raises(UnexpectedStatus):
        delete_objects(client, "member_v", [prop1hash])
    with pytest.raises(UnexpectedStatus):
        delete_objects(client, "member_v", [meta1hash])

    delete_objects(client, "member_v", [prop1hash, meta1hash])
