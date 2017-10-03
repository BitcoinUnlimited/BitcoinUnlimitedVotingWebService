import time
from functools import wraps
import pytest
from appmaker import make_test_app
import config
from butype import *
from butypes import *
import bitcoin
import gpglayer
import testkeys

def makeTestKey(name):
    privkey=bitcoin.hex_to_b58check(
            bitcoin.sha256(name), 0x80)
    
    address = bitcoin.privkey_to_address(privkey)

    return privkey, address

def makeTestAction(
        author,
        apart,
        pgp = False):
    """ Create signed test action where privkey of author equals sha256(author). """

    action_string = config.action_prefix + apart
    privkey = bitcoin.sha256(author.name)

    if pgp: # use PGP signature
        assert author.name in ["member_a", "member_b"]
        gpg = gpglayer.gpgInstance()
        ki1 = gpg.import_keys(testkeys.privkey1)
        ki2 = gpg.import_keys(testkeys.privkey2)

        signature = gpg.sign(action_string,
                             keyid = (
                                 ki1.fingerprints[0] if author.name=="member_a" else ki2.fingerprints[0]),
                             detach=True,
                             passphrase="123").data.decode("ascii")

        assert len(signature)
    else:
        signature = bitcoin.ecdsa_sign(action_string, privkey)
    
    return Action(
                 author = author,
                 action_string = action_string,
                 signature = signature)

def makeTestMultiAction(author,
                        aparts):
    """ Create signed multi action with privkey of authors as for makeTestAction. """
    multi_action_string = config.action_prefix+ (
        "\n@@@@@\n"+config.action_prefix).join(aparts)
    
    privkey = bitcoin.sha256(author.name)
    multi_signature = bitcoin.ecdsa_sign(multi_action_string, privkey)

    return MultiAction(
        author = author,
        multi_action_string = multi_action_string,
        multi_signature = multi_signature)

    
def makeTestMemberKeys():
    member_names=["member_%s" % x for x in "abcdefghijklmnopqrstuvwxyz"]

    privkeys=[
        bitcoin.hex_to_b58check(
            bitcoin.sha256(member), 0x80)
        for member in member_names]
    
    addresses=[bitcoin.privkey_to_address(priv) for priv in privkeys]

    return member_names, addresses, privkeys

def makeTestMemberList(old_ml, old_vote_times=True):
    member_names, addresses, privkeys = makeTestMemberKeys()

    secretary="member_s"
    president="member_p"
    developer="member_d"
    votemasters=["member_v", "member_w", "secretary"]

    t=time.time()
    members = []
    for (name, addr) in zip(member_names, addresses):
        try:
            m = Member.by_name(name)
            if m.address != addr:
                raise Exception("Member with different addresses.")
        except:
            if name == "member_a":
                m = Member(name, addr, testkeys.pubkey1)
            elif name == "member_b":
                m = Member(name, addr, testkeys.pubkey2)
            else:
                m = Member(name, addr)
           
        members.append(m)
        if old_vote_times:
            Global.set_member_last_vote_time(m, t)

    secretary = members[ord('s')-ord('a')]
    president = members[ord('p')-ord('a')]
    developer = members[ord('d')-ord('a')]

    
    ml=MemberList(
        members = members,
        secretary = secretary,
        president = president,
        developer = developer,
        previous = old_ml)
    Global.set_votemaster_rules(votemasters)
    
    db.session.add(ml)
    db.session.commit()

    return ml

class DummyUpload:
    def __init__(self, filename, content_type):
        self.filename = filename
        self.content_type = content_type

@pytest.fixture(scope="function")
def app_and_session():
    """ Big session, pre-filled with test_scenario1. """
    import serve
    
    app, db = serve.make_app(test_mode_internal=True)
    import logging
    logging.basicConfig(level=logging.INFO)

    import test_scenarios
    test_scenarios.test_scenario1(db.session, "")

    logging.basicConfig(level=logging.DEBUG) # FIXME: use ctx manager
    db.session.commit()
    
    return app, db.session

@pytest.fixture(scope="function")
def small_app():
    """ Flask app and session, only pre-filled with default initial member list. """
    import serve
    
    app, db = serve.make_app(test_mode_internal=True)

    from test_tmemberlist import makeTestMemberList
    ml = makeTestMemberList(None)
    ml.set_current()
    db.session.add(ml)
    db.session.commit()
    
    return app

@pytest.fixture(scope="function")
def app():
    """ App, with DB prefilled with test_scenario1. """
    app, session = app_and_session()
    return app

@pytest.fixture(scope="function")
def bare_session():
    """ Session without any predefined stuff. """
    import serve
    
    app, db = serve.make_app(test_mode_internal=True)
    return db.session


@pytest.fixture(scope="function")
def member_list():
    ml = Global.current_member_list()
    if ml is None:
        ml = makeTestMemberList(None)
        Global.set_current_member_list(ml)
    return ml

@pytest.fixture(scope="function")
def member_list_no_vote_times():
    ml = Global.current_member_list()
    if ml is None:
        ml = makeTestMemberList(None, False)
        Global.set_current_member_list(ml)
    return ml

def objCached(cls, name):
    def decorator(objmaker):
        @wraps(objmaker)
        def wrapper():
            n = "test_"+name+"_hash"
            try:
                href = Global.get(n)
                obj = cls.by_hash(href)
                return obj
            except KeyError:
                obj = objmaker()
                db.session.add(obj)
                Global.set(n, obj.hashref())
                return obj
            
        return wrapper
    return decorator

@pytest.fixture(scope="function")
@objCached(RawFile, "raw_file")
def raw_file():
    return RawFile(b"test data")

@pytest.fixture(scope="function")
def member_a():
    member_list() # make sure member exists
    return Member.by_name(name="member_a")

@pytest.fixture(scope="function")
def member_v():
    member_list() # make sure member exists
    return Member.by_name(name="member_v")

@pytest.fixture(scope="function")
@objCached(Member, "newmember5")
def newmember5():
    nm1addr=makeTestKey("newmember5")[1]
    return Member("newmember5", nm1addr)
    

@pytest.fixture(scope="function")
@objCached(ProposalMetadata, "proposal_metadata")
def proposal_metadata():
    rf=raw_file()
    ml=member_list()
    return ProposalMetadata("testfile.pdf",
                            "application/pdf",
                            rf,
                            makeTestAction(member_a(),
                                           "%s proposal-upload file %s by member_a"
                                           % (ml.hashref(), rf.hashref())))


@pytest.fixture(scope="function")
@objCached(ProposalVoteResult, "proposal_vote_result")
def proposal_vote_result():
    ml = member_list()
    pm = proposal_metadata()
    pv=ProposalVote(raw_file(), pm,
                    makeTestAction(member_v(),
                                   "%s open-proposal-vote meta %s by member_v method (buip-acc-rej-abs)" % (ml.hashref(), pm.hashref())) , "buip-acc-rej-abs", [])
    pvr = ProposalVoteResult(pv)
    return pvr

@pytest.fixture(scope="function")
@objCached(ProposalVote, "proposal_vote")
def proposal_vote():
    return proposal_vote_result().vote

def proposal_vote_ballot(pvr):
    ml=member_list()
    # Important note: ProposalVoteResult *changes* when voting!
    return makeTestAction(member_a(),
                          "%s cast-proposal-ballot vote %s by member_v answer (accept)" %
                          (ml.hashref(), pvr.vote.hashref()))


@pytest.fixture(scope="function")
@objCached(Action, "propose_member_action")
def propose_member_action():
    ml = member_list()
    
    return makeTestAction(member_v(), "%s propose-member name %s address %s by member_v" % (
        ml.hashref(), newmember5().name, newmember5().address))

@pytest.fixture(scope="function")
@objCached(Action, "member_ballot")
def member_ballot():
    ml = member_list()
    
    return makeTestAction(member_a(), "%s cast-member-ballot name %s address %s by member_a answer accept" % (
        ml.hashref(), newmember5().name, newmember5().address))

    
@pytest.fixture(scope="function")
@objCached(MemberElectionResult, "member_election_result")
def member_election_result():
    ml = member_list()

    return MemberElectionResult(
        newmember5(),
        propose_member_action())




