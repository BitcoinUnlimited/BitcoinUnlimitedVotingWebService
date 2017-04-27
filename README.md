# BUVWEB - Bitcoin Unlimited Voting web service (PUBLIC ALPHA)

Author: Awemany  <<awemany@protonmail.com>>

## Introduction

This is an implementation of a and hopefully the voting tool for the
Bitcoin Unlimited organisation.

The ideas in this work are partly based upon an earlier, older prototype
named 'buv', which is available here: 

[https://github.com/awemany/buv](https://github.com/awemany/buv)

## Features

  - It is implemented as a meant-to-be-public web service, written in
    Python3 using the Flask microframework and SQLAlchemy on top of
    SQLite for the database part. HTML is rendered through
    jinja2. Vitalik Buterin's pybitcoin library is used for the
    server-side handling of Bitcoin addresses and message signing. On
    the client side, the bitcoinjs library is used for optional
    message signing. Tests are done using py.test and the coverage
    module.

    Furthermore, a simple, minor change to the current web site code
    exists (see voting branch of this BitcoinUnlimitedWeb clone here:
    [https://github.com/awemany/BitcoinUnlimitedWeb](https://github.com/awemany/BitcoinUnlimitedWeb))
    to simply forward resp. proxy the /voting URL subspace of the
    BitcoinUnlimited website to this software.

    Details of the integration into the main bitcoinunlimited.info
    website are TBD.

  - All interaction with the server (after initial setup) happens
    through messages that are Bitcoin-signed by BU members, named
    *actions*. A designated role 'votemaster' has been implemented,
    which is the member that organises elections on BUIPs and new
    members. This role is currently the same as the BU secretary. It
    has been logically separated from this role to allow for potential
    future changes regarding responsibility in the BU articles.
        
    The message submission happens through a single endpoint, which
    should cut down on the attack surface.

  - The actions are specially formatted, but otherwise
    human-readable clear-text strings, following a list of
    templates. The format of these actions and the corresponding
    templates is described in further detail below.

  - For all important actions (opening/closing member elections and
    proposal votes, casting ballots), pre-made forms with all
    important fields prefilled and/or precalculated have been made, to
    make it simple to interact with buvweb.

    The preferable process to sign the messages is **offline**,
    however functionality has been implemented as per BUIP FIXME to
    also allow online signing of messages using the respective
    member's BU private voting key.  Note that this is DANGEROUS and
    should be avoided by members, if possible. At the moment, it is
    also not sufficiently tested yet.

    A generic form to submit any action is available as well.
    
  - A 'paper trail' is made for all proposal votes and membership
   votes. A finished vote/election can be downloaded as a
   self-contained ZIP file of easy-to-check JSON text files, which in
   turn describe the vote data. Relationships between objects are
   expressed using SHA256 hashes, linking votes together into
   verifiable DAGs.
   
  - The currently code has full 100% (or close to) test coverage,
    including branch coverage. It is aimed for this to be an
    invariant...

  - Some care has been taken to adopt as much from the current website
    design-wise as possible. With some extra work, it should be
    possible to integrate the voting tool nicely into the rest of the
    website (which is currently under redesign and rewrite by others).
  
TODOs, bugs, downsides, and state of affairs:

  - Biggest one: The code is untested yet! I invite *everyone* to a
  review of this code. Areas of special interest are, of course,
  potential remote exploits of the python server, exploits or bugs in
  the client-side JS code, or bugs in the handling and processing of
  actions and the crypto parts.

  - The database schema normalization and in general database layout might
    need additional thought by someone more experienced in this area.

  - The code as-is is fast enough to be fully usable, but likely slow
    enough to be a major load factor on any webserver, if no
    sufficient DDOS protection and caching scheme is implemented on
    top.
    
  - Some elements are missing still: For example, functionality to
    kick out members might be needed at some point. Also, the election
    of positions and roles in BU (President, Secretary, ...) is still
    missing.
    
  - All closed votes should be timestamped into the blockchain.

  - No way to delete unneeded or unwanted objects yet.
  
  - Other minor limitations (such as on rejoining members).
  
  
## Architectural overview

All important functionality and the data is presented as a set of
simple, mostly JS-free (except for the optional online signing in
submission forms) template-generated dynamic web pages.

A set of API entry points that can be automatically used for testing
purposes or other use has been implemented as well.


The main types in buvweb are: *Member*s to represent BU members,
*MemberList*s to represent the current set of members and *Action*s to
implement actions, such as opening and closing of votes, or casting
ballots.

Proposals are represented as *RawFile*s plus attached
*ProposalMetadata*. Votes on proposals are *ProposalVote*s and the
result of the voting is a *ProposalVoteResult*.

Member elections are represented as *MemberElectionResult*s. Closing
a member election might result in a new *MemberList*.

All of these above types (except for the *RawFile*, which is just a
binary data blob) can be rendered into human-readable and easy to
understand JSON text.

References between the above objects are done using SHA256 hashes of
the respective object's JSON that is being linked to.

Furthermore, functionality has been implemented to retrieve ZIP
archives of any part of the DAG that forms from the hash-linked object
graph, such as a vote on a new member that (implicitly) includes the
result and all the current member's ballots.

## Classes and data types in detail

### Member

A member is a pair of (Member-nickname,
Bitcoin-address-for-voting).

Eligibility: A member is eligible in BUVWEB if it s/he has voted
within the last year (365 days) and is a current member.

A special, per-member-nick global value can be set to determine the
eligibility of members that have not yet voted using this system
(which will be all members, initially).

This time stamp has not been made part of the Member object itself to
keep members consistent across multiple proposal votes, and make
following the paper trail easier (same member JSON for different
elections).

Currently, member nicks and Bitcoin addresses are unique and if a
member loses a key or expires, that member needs to select a new key
and address if rejoining.

### Member list

A member list is a list of Member objects. In addition, there is
a global pointer to the *current member list*.

If a member list changes (e.g. by a new member being elected), a field
that references to the older member list is included, to build a
simply-linked list of member lists.

*Action*s (below) can only be submitted to the service if they
originate from a member that is eligible (thus current), and are
well-formed and furthermore pass all checks on the objects they should
act upon.

It should be noted that the current member list contains all current
members and *also* contains those members that are expired but have
not been explicitely kicked out.

### Action

All submissions to the service are called actions. An action has an
author (a member), a text string "action string" describing the
action, a signature and a reference to the member list that was
current when this action was submitted.

It furthermore has a time stamp (UNIX epoch) that is filled in by the
server when the action is submitted.

After receiving an action, the action parser matches incoming actions
against templates, extracts and validates data types from the action
and executes the correct handling code.

All changes to the system, opening or closing of votes, proposal
uploads as well as ballots cast are actions.

The action string is prefixed with a special marker string to distinguish
BU voting actions from anything else a BU member might have voted on.

This string is `"bitcoin-unlimited-voting: "` for the to-be-setup live
voting system, and
`"bitcoin-unlimited-voting-test-data-without-relevance: "` for any
test system.

### RawFile

A representation of a binary chunk of data / file. If referenced by
any other object, the SHA256sum of the whole contents is taken.


### ProposalMetadata

Meta data for a proposal vote that is created right along with the
RawFile for a `proposal-upload` action. Contains the file name, MIME
type, creating action and a reference to the raw file.

It also contains a flag whether a proposal is public (and only then is
it visible to the world). This flag needs to be set using the
'proposal-publish' action by the vote master.

### ProposalVote

An opened vote on a BUIP proposal. Refers the proposal meta data. Has
a voting method name (currently just `buip-acc-rej-abs` for BUIP vote,
acception/reject/abstain/spoil), potential options for the voting method
(currently none).

### ProposalVoteResult

Result of a vote on a proposal, *including intermediate* results. Has
a set of ballots cast on the proposal, and links to the ProposalVote.

### MemberElectionResult

Member election, including result. Refers the member to elect and a
set of ballots cast. Furthermore contains a flag whether the member
election is open or closed (done).


### Global

Hodls global data. Currently, this is the pointer to the current
member list, as well as the last-voted-times of those members that
have not yet voting in the BUVWEB system.

## The action parser and action types

The action parser dissects the action string and does type checks (as
defined in `atypes.py`). 

It is a simple template-matching specification 'language' that allows
to nest templates (using parenthesis) and repeat a type (for simple
lists of objects) by enclosing the variable in `[ ]` square brackets.

Variables are marked with the percentage `%` sign, the variable name
and the variable's type.

Text that is not specifically marked has to match as-is.

More specifically, the following action template patterns are defined:

- `proposal-upload file %file_hash:sha256 by
  %member:current_member`: Upload of a proposal by a current
  member. The uploaded data (that has to be uploaded allong with the
  signed action) is referred by its SHA256 hash, which will be put
  into the `file_hash` variable internally. The action needs a current
  member, which will be in the `member` variable.

- `proposal-publish file %file_hash:sha256 by
  %member:votemaster`: Publish a proposal (only by the current votemaster).

- `open-proposal-vote meta %meta_hash:sha256 by %member:votemaster
  method (method:votemethod)`: Open a vote on a BUIP, by the current
  votemaster. Needs to refer to the current proposal metadata
  hash. The vote method can currently only be the simple string
  `buip-acc-rej-abs`.
  
- `close-proposal-vote result %result_hash:sha256 by %member:votemaster`:
  Closes a vote on a proposal and thus makes the result final (by the
  votemaster).
  It refers to the current (changing) result hash, also to make sure
  the votemaster is aware of the status of the proposal vote.
  
- `cast-proposal-ballot vote %vote_hash:sha256 by
  %member:current_member answer (answer_tuple:voteanswer)`: Action by
  a member that represents a ballot cast on a BUIP.

- `propose-member name %name:membername address %address:address by
  %member:votemaster`: The vote master proposes a new member and opens
  the election on that member.
  
- `cast-member-ballot name %name:membername address %address:address
  by %member:current_member answer %answer_tuple:member_acc_rej_abs`:
  A member casts a ballot in the election of a single new member.

- `close-member-elections all [names:membername] by %member:votemaster`:
  The vote master closes all member elections at once, yielding a new
  current member list. This is currently the only way to close member
  elections.
  

## File overview

The webserver is started through the command line driver `buvcmd.py`,
which in turns hands control over to Flask in `serve.py`. All web
endpoints are defined and registered in `serve.py`. All endpoints are
in the `api1/` URL space, from the POV of this webservice.

Objects such as Members and Actions are implemented in files named
`t<object-name>.py` with the respective `object-name`.

A common supertype with common methods is defined as `BUType` in
`butype.py`. The collection of all subtypes is available in `butypes.py`.

Test code is usally placed next to a given python file by placing the
prefix `test_` in front.

A simple test scenario is created and exercised in
`test_scenarios.py`. An even more high-level test using the web-API is
executed in `test_hl1.py`.

The action parser is implemented in `actionparser.py` and the more
generic parts in `aparser.py`. The latter is also used to parse vote
method specification substrings. Code to execute actions rests in
`actionexec.py`. Type definitions are in `atypes.py`.

Important global configuration settings are in `config.py`.

There is a test environment that can be generated for local testing
using the `testenv.py` script.



