#!/usr/bin/env python3
# Create dummy test environment
import os
import logging
logging.basicConfig(level=logging.DEBUG)
import hashlib
import sqlalchemy.exc
import pytest
import json
import config
from butypes import *
from butype import *
from test_tmemberlist import makeTestMemberList, makeTestKey
from test_helpers import DummyUpload
from test_taction import makeTestAction
from test_helpers import bare_session, makeTestMultiAction
from jvalidate import ValidationError
import testkeys

# FIXME: refactor this mess by creating suitable fixtures

def test_scenario1(bare_session, stopper=""):
    old_ml = makeTestMemberList(None) # dummy old member list

    ml = makeTestMemberList(old_ml)
    ml.set_current()

    proposal1=b"Test proposal #1"
    hashprop1=hashlib.sha256(proposal1).hexdigest()

    du=DummyUpload("test_proposal_1.txt", "text/plain")
    act_upload=makeTestAction(author=Member.by_name("member_a"),
                              apart =
                              (ml.hashref()+" proposal-upload file %s by member_a" % hashprop1),
                              pgp = True)
    act_upload.apply(du, proposal1)
    bare_session.commit()

    proposal2=b"Test proposal #2"
    hashprop2=hashlib.sha256(proposal2).hexdigest()
    du=DummyUpload("test_proposal_2.txt", "text/plain")
    act_upload=makeTestAction(author=Member.by_name("member_b"),
                              apart =
                              (ml.hashref()+" proposal-upload file %s by member_b" % hashprop2),
                              pgp = True)
    act_upload.apply(du, proposal2)
    bare_session.commit()

    if stopper == "two-unpublished":
        return

    rf= RawFile.by_hash(hashprop1)
    m1 = rf.proposal_metadata

    act_publish=makeTestAction(author=Member.by_name("member_v"),
                               apart =
                               (ml.hashref()+" proposal-publish file %s designation BUIP0001 title 'some annoyingly long title for BUIP0001 to test the proper formatting in all templates' by member_v" % hashprop1))
    act_publish.apply(None, None)
    bare_session.commit()

    if stopper == "one-published":
        return

    act_open_vote=makeTestAction(author=Member.by_name("member_v"),
                                 apart =
                                 (ml.hashref()+
                                  " open-proposal-vote meta %s by member_v method (buip-acc-rej-abs)" %
                                  (rf.proposal_metadata.hashref())))
    vote = act_open_vote.apply(None, None)
    bare_session.commit()
    if stopper == "open-proposal-vote":
        return vote


    vdeps=vote.dependencies()
    assert len(vdeps) == 4
    assert rf in vdeps
    assert rf.proposal_metadata in vdeps
    assert act_open_vote in vdeps
    assert vote.result in vdeps

    for i, x in enumerate("abcdefghijklmnopqrstu"):
        if i<10:
            answer="accept"
        else:
            answer="reject"

        act_cast_vote=makeTestAction(author=Member.by_name("member_%s" % x),
                                     apart =
                                     (ml.hashref()+
                                      " cast-proposal-ballot vote %s by member_%s answer (%s)" %
                                      (vote.hashref(), x, answer)))
        act_cast_vote.apply(None, None)
        bare_session.commit()
    if stopper == "votes-cast":
        return

    act_close_vote=makeTestAction(author=Member.by_name("member_v"),
                                 apart =
                                 (ml.hashref()+
                                  " close-proposal-vote result %s by member_v" %
                                  (vote.result.hashref())))

    act_close_vote.apply(None, None)
    bare_session.commit()

    act_new_member=makeTestAction(author=Member.by_name("member_v"),
                                 apart =
                                 (ml.hashref()+
                                  " propose-member name newmember1 address %s by member_v" %
                                  (makeTestKey("newmember1")[1])))
    act_new_member.apply(None, None)
    act_new_member=makeTestAction(author=Member.by_name("member_v"),
                                 apart =
                                 (ml.hashref()+
                                  " propose-member name newmember2 address %s by member_v" %
                                  (makeTestKey("newmember2")[1])))
    act_new_member.apply(None, None)
    act_new_member=makeTestAction(author=Member.by_name("member_v"),
                                 apart =
                                 (ml.hashref()+
                                  " propose-member name newmember3 address %s by member_v" %
                                  (makeTestKey("newmember3")[1])))
    act_new_member.apply(None, None)
    bare_session.commit()
    if stopper == "new-applicants":
        return

    for i, x in enumerate("abcdefghijklmnopq"):
        ans=["accept", "reject"][i&1]
        act_new_member_cast=makeTestAction(author=Member.by_name("member_%s" % x),
                                     apart =
                                     (ml.hashref()+
                                      " cast-member-ballot name newmember1 address %s by member_%s answer %s" % (
                                      (makeTestKey("newmember1")[1], x, ans))))
        act_new_member_cast.apply(None, None)
        bare_session.commit()
    if stopper == "votes-on-applicant":
        return

    act_close_member_elections=makeTestAction(
        author=Member.by_name("member_v"),
        apart =
        (ml.hashref()+
         " close-member-elections all [newmember1 newmember2 newmember3] by member_v"))
    act_close_member_elections.apply(None, None)

    assert Global.current_member_list() != ml
    assert Member.by_name("newmember1") in Global.current_member_list().members

    bare_session.commit()


def test_deps(bare_session):
    test_scenario1(bare_session)

    all_objs = set(get_all_objects().values())
    for obj in all_objs:
        for dep in obj.dependencies():
            assert dep in all_objs

def test_renders(bare_session):
    test_scenario1(bare_session)
    all_objs = set(get_all_objects().values())
    for obj in all_objs:
        assert isinstance(obj.extraRender(),  dict)

def test_public(bare_session):
    test_scenario1(bare_session)
    all_objs = set(get_all_objects().values())
    for obj in all_objs:
        assert obj.public() or isinstance(obj, RawFile)

def test_serialized(bare_session):
    test_scenario1(bare_session)
    all_objs = set(get_all_objects().values())
    for obj in all_objs:
        ser = obj.serialize()
        assert isinstance(ser, bytes)
        if not isinstance(obj, RawFile):
            json.loads(ser.decode("utf-8"))


def test_scenario_invalid1(bare_session):
    """ Test invalid action type """
    ml = makeTestMemberList(None)
    ml.set_current()

    proposal1=b"Test proposal #1"
    hashprop1=hashlib.sha256(proposal1).hexdigest()

    du=DummyUpload("test_proposal_1.txt", "text/plain")
    with pytest.raises(ValidationError):
        act_upload_invalid=makeTestAction(author=Member.by_name("member_a"),
                                          apart =
                                          (ml.hashref()+" proposal-download file %s by member_a" % hashprop1))

        act_upload_invalid.apply(None, None)


def test_invalid_scenario2(bare_session):
    """ Test (invalid) two votes on one proposal. """
    ml = makeTestMemberList(None)
    ml.set_current()

    proposal1=b"Test proposal #1"
    hashprop1=hashlib.sha256(proposal1).hexdigest()

    du=DummyUpload("test_proposal_1.txt", "text/plain")
    act_upload=makeTestAction(author=Member.by_name("member_a"),
                              apart =
                              (ml.hashref()+" proposal-upload file %s by member_a" % hashprop1))
    act_upload.apply(du, proposal1)
    bare_session.commit()

    rf= RawFile.by_hash(hashprop1)

    act_publish=makeTestAction(author=Member.by_name("member_v"),
                               apart =
                               (ml.hashref()+" proposal-publish file %s designation BUIP0001 title 'title BUIP0001' by member_v" % hashprop1))
    act_publish.apply(None, None)
    bare_session.commit()

    act_open_vote=makeTestAction(author=Member.by_name("member_v"),
                                 apart =
                                 (ml.hashref()+
                                  " open-proposal-vote meta %s by member_v method (buip-acc-rej-abs)" %
                                  (rf.proposal_metadata.hashref())))
    vote = act_open_vote.apply(None, None)

    with pytest.raises(ValidationError):
        act_open_vote2=makeTestAction(author=Member.by_name("member_v"),
                                      apart =
                                     (ml.hashref()+
                                      " open-proposal-vote meta %s by member_v method (buip-acc-rej-abs)" %
                                      (rf.proposal_metadata.hashref())))
        act_open_vote2.apply(None, None)

def test_scenario_invalid3(bare_session):
    test_scenario1(bare_session, "two-unpublished")
    ml=Global.current_member_list()

    proposal1=b"Test proposal #1"
    hashprop1=hashlib.sha256(proposal1).hexdigest()
    rf= RawFile.by_hash(hashprop1)

    with pytest.raises(ValidationError):
        act_open_vote=makeTestAction(author=Member.by_name("member_v"),
                                     apart =
                                     (ml.hashref()+
                                      " open-proposal-vote meta %s by member_v method (buip-acc-rej-abs)" %
                                      (rf.proposal_metadata.hashref())))
        act_open_vote.apply(None, None)

def test_invalid_publish(bare_session):
    test_scenario1(bare_session, stopper="two-unpublished")
    ml=Global.current_member_list()

    proposal1=b"Test proposal #1"
    hashprop1=hashlib.sha256(proposal1).hexdigest()

    hashprop_noexist = hashlib.sha256(b"nope").hexdigest()

    rf= RawFile.by_hash(hashprop1)
    m1 = rf.proposal_metadata

    # test hash does not exist
    with pytest.raises(ValidationError):
        act_publish=makeTestAction(author=Member.by_name("member_v"),
                                   apart =
                                   (ml.hashref()+" proposal-publish file %s designation BUIP0001 title 'title BUIP0001' by member_v" % hashprop_noexist))
        act_publish.apply(None, None)

    rf_nomd = RawFile(b"nope")
    bare_session.add(rf_nomd)
    bare_session.commit()

    # test file has no metadata
    with pytest.raises(ValidationError):
        act_publish=makeTestAction(author=Member.by_name("member_v"),
                                   apart =
                                   (ml.hashref()+" proposal-publish file %s designation BUIP0001 title 'title BUIP0001' by member_v" % hashprop_noexist))
        act_publish.apply(None, None)

    # test file is already public
    m1.file_public = True

    with pytest.raises(ValidationError):
        act_publish=makeTestAction(author=Member.by_name("member_v"),
                                   apart =
                                   (ml.hashref()+" proposal-publish file %s designation BUIP0001 title 'title BUIP0001' by member_v" % hashprop1))
        act_publish.apply(None, None)


def test_invalid_open_proposal_vote(bare_session):
    test_scenario1(bare_session, stopper="one-published")
    ml=Global.current_member_list()

    proposal1=b"Test proposal #1"
    hashprop1=hashlib.sha256(proposal1).hexdigest()

    hashprop_noexist = hashlib.sha256(b"nope").hexdigest()

    # open proposal vote on invalid metadata
    with pytest.raises(ValidationError):
        act_open_vote=makeTestAction(author=Member.by_name("member_v"),
                                     apart =
                                     (ml.hashref()+
                                      " open-proposal-vote meta %s by member_v method (buip-acc-rej-abs)" %
                                      (hashprop_noexist)))
        act_open_vote.apply(None, None)

def test_invalid_open_proposal_vote(bare_session):
    test_scenario1(bare_session, stopper="one-published")
    ml=Global.current_member_list()

    proposal1=b"Test proposal #1"
    hashprop1=hashlib.sha256(proposal1).hexdigest()

    hashprop_noexist = hashlib.sha256(b"nope").hexdigest()

    rf= RawFile.by_hash(hashprop1)
    m1 = rf.proposal_metadata

    # open proposal vote on invalid metadata
    with pytest.raises(ValidationError):
        act_open_vote=makeTestAction(author=Member.by_name("member_v"),
                                     apart =
                                     (ml.hashref()+
                                      " open-proposal-vote meta %s by member_v method (buip-acc-rej-abs)" %
                                      (hashprop_noexist)))
        act_open_vote.apply(None, None)

    # open proposal vote on non-public file
    m1.file_public=False
    with pytest.raises(ValidationError):
        act_open_vote=makeTestAction(author=Member.by_name("member_v"),
                                     apart =
                                     (ml.hashref()+
                                      " open-proposal-vote meta %s by member_v method (buip-acc-rej-abs)" %
                                      (rf.proposal_metadata.hashref())))
        act_open_vote.apply(None, None)


    m1.file_public=True
    act_open_vote=makeTestAction(author=Member.by_name("member_v"),
                                     apart =
                                     (ml.hashref()+
                                      " open-proposal-vote meta %s by member_v method (buip-acc-rej-abs)" %
                                      (rf.proposal_metadata.hashref())))
    act_open_vote.apply(None, None)

    # open proposal vote where vote is open already
    with pytest.raises(ValidationError):
        act_open_vote=makeTestAction(author=Member.by_name("member_v"),
                                     apart =
                                     (ml.hashref()+
                                      " open-proposal-vote meta %s by member_v method (buip-acc-rej-abs)" %
                                      (rf.proposal_metadata.hashref())))
        act_open_vote.apply(None, None)

def test_invalid_close_proposal_vote(bare_session):
    vote = test_scenario1(bare_session, stopper="open-proposal-vote")
    ml=Global.current_member_list()

    proposal1=b"Test proposal #1"
    hashprop1=hashlib.sha256(proposal1).hexdigest()

    hashprop_noexist = hashlib.sha256(b"nope").hexdigest()

    rf= RawFile.by_hash(hashprop1)
    m1 = rf.proposal_metadata

    # close vote on proposal that does not exist
    with pytest.raises(ValidationError):
        act_close_vote=makeTestAction(author=Member.by_name("member_v"),
                                      apart =
                                 (ml.hashref()+
                                  " close-proposal-vote result %s by member_v" %
                                  (hashprop_noexist)))
        act_close_vote.apply(None, None)

    # close vote twice
    act_close_vote=makeTestAction(author=Member.by_name("member_v"),
                                  apart =
                                  (ml.hashref()+
                                   " close-proposal-vote result %s by member_v" %
                                   (vote.result.hashref())))
    act_close_vote.apply(None, None)
    bare_session.commit()

    with pytest.raises(ValidationError):
        act_close_vote=makeTestAction(author=Member.by_name("member_v"),
                                      apart =
                                 (ml.hashref()+
                                  " close-proposal-vote result %s by member_v" %
                                  (vote.result.hashref())))
        act_close_vote.apply(None, None)


def test_invalid_cast_ballot(bare_session):
    vote = test_scenario1(bare_session, stopper="open-proposal-vote")
    ml=Global.current_member_list()

    proposal1=b"Test proposal #1"
    hashprop1=hashlib.sha256(proposal1).hexdigest()

    hashprop_noexist = hashlib.sha256(b"nope").hexdigest()

    rf= RawFile.by_hash(hashprop1)
    m1 = rf.proposal_metadata

    # cast ballot for non-existing vote
    with pytest.raises(ValidationError):
        x="a"
        act_cast_vote=makeTestAction(author=Member.by_name("member_%s" % x),
                                     apart =
                                     (ml.hashref()+
                                      " cast-proposal-ballot vote %s by member_%s answer (%s)" %
                                      (hashprop_noexist, x, "accept")))
        act_cast_vote.apply(None, None)

def test_invalid_cast_member_ballot(bare_session):
    vote = test_scenario1(bare_session, stopper="new-applicants")
    ml=Global.current_member_list()

    proposal1=b"Test proposal #1"
    hashprop1=hashlib.sha256(proposal1).hexdigest()

    hashprop_noexist = hashlib.sha256(b"nope").hexdigest()

    rf= RawFile.by_hash(hashprop1)
    m1 = rf.proposal_metadata

    # create ballot for member election that does not exist
    with pytest.raises(ValidationError):
        ans="accept"
        x="a"
        act_new_member_cast=makeTestAction(author=Member.by_name("member_%s" % x),
                                     apart =
                                     (ml.hashref()+
                                      " cast-member-ballot name member_b address %s by member_%s answer %s" % (
                                      (makeTestKey("member_b")[1], x, ans))))
        act_new_member_cast.apply(None, None)

    # create ballot with member_name<->address mismatch
    with pytest.raises(ValidationError):
        ans="accept"
        x="a"
        act_new_member_cast=makeTestAction(author=Member.by_name("member_%s" % x),
                                     apart =
                                     (ml.hashref()+
                                      " cast-member-ballot name member_c address %s by member_%s answer %s" % (
                                      (makeTestKey("member_b")[1], x, ans))))
        act_new_member_cast.apply(None, None)

    # two ballots by same voter
    nml=Global.current_member_list()
    with pytest.raises(ValidationError):
        ans="accept"
        x="a"
        act_new_member_cast=makeTestAction(author=Member.by_name("member_%s" % x),
                                     apart =
                                     (nml.hashref()+
                                      " cast-member-ballot name newmember1 address %s by member_%s answer %s" % (
                                      (makeTestKey("newmember1")[1], x, ans))))
        act_new_member_cast.apply(None, None)

        act_new_member_cast=makeTestAction(author=Member.by_name("member_%s" % x),
                                     apart =
                                     (nml.hashref()+
                                      " cast-member-ballot name newmember1 address %s by member_%s answer %s" % (
                                      (makeTestKey("newmember1")[1], x, ans))))
        act_new_member_cast.apply(None, None)


    act_close_member_elections=makeTestAction(
        author=Member.by_name("member_v"),
        apart =
        (ml.hashref()+
         " close-member-elections all [newmember1 newmember2 newmember3] by member_v"))
    act_close_member_elections.apply(None, None)


    # create ballot for closed vote
    nml=Global.current_member_list()
    with pytest.raises(ValidationError):
        ans="accept"
        x="a"
        act_new_member_cast=makeTestAction(author=Member.by_name("member_%s" % x),
                                     apart =
                                     (nml.hashref()+
                                      " cast-member-ballot name newmember1 address %s by member_%s answer %s" % (
                                      (makeTestKey("newmember1")[1], x, ans))))
        act_new_member_cast.apply(None, None)


def test_invalid_member_vote_close(bare_session):
    vote = test_scenario1(bare_session, stopper="votes-on-applicant")
    ml=Global.current_member_list()

    with pytest.raises(ValidationError):
        act_close_member_elections=makeTestAction(
            author=Member.by_name("member_v"),
            apart =
            (ml.hashref()+
             " close-member-elections all [] by member_v"))
        act_close_member_elections.apply(None, None)

def test_update_ml_address(bare_session):
    test_scenario1(bare_session, stopper="two-unpublished")
    ml = Global.current_member_list()

    new_privkey, new_address = makeTestKey("some-new-key")

    old_member =  Member.by_name("member_a")
    cur_address = Member.by_name("member_a").address

    assert old_member.most_recent

    assert cur_address != new_address

    act_newaddr = makeTestAction(author = Member.by_name("member_v"),
                                 apart = (
                                     ml.hashref() +
                                     " update-memberlist-set-address address %s for member_a by member_v" % new_address))
    act_newaddr.apply(None, None)

    cur_address = Member.by_name("member_a").address
    assert cur_address == new_address
    assert not old_member.most_recent
    assert old_member not in Global.current_member_list().members
    assert Member.by_name("member_a").pgp_pubkey is not None

def test_update_ml_pgpkey(bare_session):
    test_scenario1(bare_session, stopper="two-unpublished")
    ml=Global.current_member_list()

    old_member =  Member.by_name("member_c")
    cur_address = Member.by_name("member_c").address
    assert Member.by_name("member_c").pgp_pubkey is None

    du=DummyUpload("new_pgp_key.txt", "text/plain")

    pubkey_hash = hashlib.sha256(testkeys.pubkey1).hexdigest()

    act_newpubkey = makeTestAction(
        author = Member.by_name("member_v"),
        apart = (ml.hashref() +
                 " update-memberlist-set-pgp-pubkey pubkey %s for member_c by member_v" % pubkey_hash))
    act_newpubkey.apply(du, testkeys.pubkey1)

    assert cur_address == Member.by_name("member_c").address
    assert Member.by_name("member_c").pgp_pubkey == testkeys.pubkey1.decode("ascii")

def test_update_ml_number(bare_session):
    test_scenario1(bare_session, stopper="two-unpublished")
    ml = Global.current_member_list()

    old_member =  Member.by_name("member_a")
    cur_number = Member.by_name("member_a").number

    assert old_member.most_recent

    assert cur_number != 12345

    act_newnum = makeTestAction(author = Member.by_name("member_v"),
                                 apart = (
                                     ml.hashref() +
                                     " update-memberlist-set-number number 12345 for member_a by member_v"))
    act_newnum.apply(None, None)

    cur_number = Member.by_name("member_a").number
    assert cur_number == 12345
    assert not old_member.most_recent
    assert old_member not in Global.current_member_list().members
    assert Member.by_name("member_a").pgp_pubkey is not None

    with pytest.raises(ValidationError):
        act_newnum = makeTestAction(author = Member.by_name("member_v"),
                                     apart = (
                                         ml.hashref() +
                                         " update-memberlist-set-number number -12345 for member_a by member_v"))
        act_newnum.apply(None, None)

def test_invalid_propose_member(bare_session):
    test_scenario1(bare_session, stopper="votes-cast")
    ml=Global.current_member_list()

    # create member with same nick as existing
    with pytest.raises(ValidationError):
        act_new_member=makeTestAction(author=Member.by_name("member_v"),
                                      apart =
                                      (ml.hashref()+
                                       " propose-member name member_a address %s by member_v" %
                                  (makeTestKey("newmember1")[1])))
        act_new_member.apply(None, None)

    # creat emember with same address as existing
    with pytest.raises(ValidationError):
        act_new_member=makeTestAction(author=Member.by_name("member_v"),
                                      apart =
                                      (ml.hashref()+
                                       " propose-member name newmember address %s by member_v" %
                                  (makeTestKey("member_a")[1])))
        act_new_member.apply(None, None)

def test_multiaction_proposal_vote(bare_session):
    """ Test acting o multiple proposals at once, using
    the MultiAction. """
    test_scenario1(bare_session, stopper="two-unpublished")

    ml=Global.current_member_list()

    proposal1=b"Test proposal #1"
    hashprop1=hashlib.sha256(proposal1).hexdigest()

    proposal2=b"Test proposal #2"
    hashprop2=hashlib.sha256(proposal2).hexdigest()

    # publish two at once
    act_publish=makeTestMultiAction(
        author=Member.by_name("member_v"),
        aparts = [
            (ml.hashref()+" proposal-publish file %s designation BUIP0001 title 'title BUIP0001' by member_v" % hashprop1),
            (ml.hashref()+" proposal-publish file %s designation BUIP0002 title 'title BUIP0002' by member_v" % hashprop2)])
    act_publish.apply()

    # open vote on both
    act_open_vote=makeTestMultiAction(
        author=Member.by_name("member_v"),
        aparts = [
            (ml.hashref()+ " open-proposal-vote meta %s by member_v method (buip-acc-rej-abs)" % (RawFile.by_hash(hashprop1).proposal_metadata.hashref())),
            (ml.hashref()+ " open-proposal-vote meta %s by member_v method (buip-acc-rej-abs)" % (RawFile.by_hash(hashprop2).proposal_metadata.hashref()))])
    votes = act_open_vote.apply()


    bare_session.commit()
