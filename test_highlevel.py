# high level testing functions for API based high-level tests
from io import BytesIO
import bitcoin
import config
from test_helpers import makeTestKey
import hashlib

prefix = config.web_prefix_internal

class UnexpectedStatus(Exception): pass

def rexpect(res, code):
    if res.status_code != code:
        ues=UnexpectedStatus("Expected HTTP status code %d, got %d." %
                             (code, res.status_code))
        ues.result = res
        raise ues


def sha256(s):
    return hashlib.sha256(s).hexdigest()

def postAction(client, astr, member, upload_data=None, upload_fn=None):
    """ Create dictionary for /action POST command. """
    privkey, address = makeTestKey(member)

    data={}
    data["author_name"] = member
    data["action_string"] = (
        config.action_prefix +
        ("%s " % current_member_list_hash(client))+
        astr)
    data["signature"] = bitcoin.ecdsa_sign(data["action_string"], privkey)
    if upload_data is not None:
        data["upload"]=(BytesIO(upload_data), upload_fn)

    result = client.post(prefix+"action", data = data)
    rexpect(result, 201)
    return result

######################################################################
## ACTIONS
def upload_proposal(client, data, filename, member):
    """ Upload proposal with contents 'data' and filename 'filename' from
    member 'member'. """
    postAction(
        client,
        "proposal-upload file %s by %s" % (sha256(data), member),
        member, upload_data = data, upload_fn = filename)


def publish_proposal(client, data, designation, title, votemaster):
    """ Publish proposal with given content as given member. """
    postAction(
        client,
        "proposal-publish file %s designation %s title '%s' by %s" % (sha256(data), designation, title, votemaster),
        votemaster)

def open_proposal_vote(client, data, votemaster, method):
    """ Open proposal for voting with given vote method. """
    postAction(
        client,
        "open-proposal-vote meta %s by %s method (%s)" % (meta_for_raw_file_hash(client, sha256(data)), votemaster, method), votemaster)


def cast_proposal_ballot(client, data, member, answer):
    """ Cast ballot on proposal vote. """
    postAction(
        client,
        "cast-proposal-ballot vote %s by %s answer (%s)" % (
            vote_for_raw_file_hash(client, sha256(data)),
            member,
            answer), member)

def close_proposal_vote(client, data, votemaster):
    """ Close proposal voting. """
    postAction(
        client,
        "close-proposal-vote result %s by %s" % (
            proposal_result_for_vote_hash(
                client,
                vote_for_raw_file_hash(client, sha256(data))),
            votemaster),
            votemaster)

def propose_member(client, votemaster, newmember):
    """ Propose a new member. """
    privkey, address = makeTestKey(newmember)
    postAction(
        client,
        "propose-member name %s address %s by %s" % (
            newmember, address, votemaster), votemaster)

def cast_member_ballot(client, member, newmember, answer):
    """ Cast vote on new member. """
    privkey, address = makeTestKey(newmember)
    postAction(
        client,
        "cast-member-ballot name %s address %s by %s answer %s" % (newmember, address, member, answer), member)


def close_member_elections(client, votemaster, newmembers):
    """ Close member elections. """
    postAction(
        client,
        "close-member-elections all [%s] by %s" % (
            " ".join(newmembers),
            votemaster), votemaster)

def delete_objects(client, votemaster, hashrefs):
    """ Delete a bunch of objects. """
    postAction(
        client,
        "delete-objects [%s] by %s" % (" ".join(hashrefs),
                                       votemaster), votemaster)

######################################################################
## QUERIES
def is_current_member(client, member):
    """ Is given member current? """
    # FIXME
    pass

def decode_response(res):
    return b"".join(res.response).decode("utf-8")

def current_member_list_hash(client):
    """ Return hash of current member list. """
    return decode_response(
        client.get(prefix+"debug/current-member-list-hash"))

def meta_for_raw_file_hash(client, rfhash):
    """ Return meta hash for raw file. """
    return decode_response(
        client.get(prefix+"debug/meta-for-raw-file/%s" % rfhash))

def vote_for_raw_file_hash(client, rfhash):
    """ Return proposal vote for  raw file hash. """
    return decode_response(
        client.get(prefix+"debug/vote-for-raw-file/%s" % rfhash))

def proposal_result_for_vote_hash(client, vhash):
    """ Return proposal vote result for vote. """
    return decode_response(
        client.get(prefix+"debug/result-for-vote/%s" % vhash))

def summary_for_proposal_vote_result(client, rhash):
    return client.get(prefix+"debug/summary-of-proposal-vote-result/%s" % rhash).json

def summary_for_member_election_result(client, rhash):
    return client.get(prefix+"debug/summary-of-member-election-result/%s" % rhash).json

def all_hashrefs_of_type(client, name):
    return client.get(prefix+"debug/hashrefs-by-type/%s" % name).json

def is_public_raw_file_hash(client, rfhash):
    metahash = meta_for_raw_file_hash(client, rfhash)
    res = client.get(prefix+"raw/proposal_metadata/%s" % metahash)
    return bool(res.json["file_public"])

def get_designation(client, rfhash):
    metahash = meta_for_raw_file_hash(client, rfhash)
    res = client.get(prefix+"raw/proposal_metadata/%s" % metahash)
    return res.json["designation"]

def get_title(client, rfhash):
    metahash = meta_for_raw_file_hash(client, rfhash)
    res = client.get(prefix+"raw/proposal_metadata/%s" % metahash)
    return res.json["title"] if "title" in res.json else None
