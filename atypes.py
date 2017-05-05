# atypes: Data type mappings (including sanitize) for
# functionality as used in actions

import re
import bitcoin
from tglobal import Global
from aparser import AExpr
from jvalidate import is_sha256, ValidationError

def tSHA256(x):
    """ A 32 byte hex-encoded value. """
    if not is_sha256(x):
        raise ValidationError("Invalid hash '%s'." % x)
    return x

def tInt(x):
    """ An integer. """
    try:
        return int(x)
    except:
        raise ValidationError("Invalid int '%s'." % x)

def tTokenList(context, x):
    """ A subexpression - returns just the token list itself. """
    if not isinstance(x, list):
        raise ValidationError("List of tokens expected, got '%s'." % x)
    return x

def tMemberName(x):
    if len(x)>30:
        raise ValidationError("Invalid member name '%s' (too long)." % x)
    
    if not re.match("^[a-zA-Z0-9_-]+$", x):
        raise ValidationError("Invalid member name '%s'." % x)

    if x in ["president", "developer", "secretary"]:
        raise ValidationError("Invalid member name '%s'. Can't be any of the official BU rules." % x)
    
    return x

def tAddress(x):
    if len(x)>35:
        raise ValidationError("Invalid address '%s' (too long)." %x)
    try:
        bitcoin.b58check_to_bin(x)
    except:
        raise ValidationError("Invalid address '%s'." % x)
    return x


def tSafeString(x):
    """ String that hopefully cannot be used to render any HTML/JS tricks. 
    FIXME: review!
    """
    if x[0]=="'":
        if x[-1] !="'":
            raise ValidationError("String starting with \"'\" needs to end with \"'\".")
    elif x[0]=='"':
        if x[-1] !='"':
            raise ValidationError("String starting with '\"' needs to end with '\"'.")
    else:
        raise ValidationError("Please put string in quote marks.")

    x=x[1:-1]

    
    if not re.match("^[a-zA-Z0-9_ .;!?+\-*/#@%=^\(\)]*$", x):
        raise ValidationError("Unsafe string '%s'." % x)
    return x

def tYesNo(x):
    """ A boolean, specified as yes(true) or no(false). """
    if x=="yes":
        return True
    elif x=="no":
        return False
    else:
        raise ValidationError("Expected yes or no, got '%s'." % x)

def tAccRejAbs(x):
    """ A value accept, reject or accept, returned as string. """
    if x in ["accept", "reject", "abstain", "spoil"]:
        return x
    else:
        raise ValidationError(
            "Expected accept, reject or abstain (or spoil), got '%s'." % x)
    

######################################################################
def tCurrentMember(membername):
    if membername not in [m.name for m in Global.current_member_list().members]:
        raise ValidationError("Member '%s' needs to be current." % membername)
    return membername

def tVoteMaster(membername):
    if membername != Global.current_member_list().votemaster.name:
        raise ValidationError("Member '%s' needs to be vote master." % membername)
    return membername

def tVoteMethod(context, tokens):
    from vote_methods import vote_methods
    methodname = tokens[0]
    tokens = tokens[1:]
    if methodname not in vote_methods:
        raise ValidationError("Invalid voting method '%s'." % methodname)

    method = vote_methods[methodname]()
    ae = AExpr(method.spec_template, atypes)
    avars = ae.parse(tokens)
    method.checkSpecification(**avars)
    return (methodname, avars)

def tVoteAnswer(context, tokens): # FIXME: code duplication
    from tproposalvote import ProposalVote
    from vote_methods import vote_methods

    if "vote_hash" not in context:
        raise ValidationError("Expected 'vote_hash' in context.")
    
    vote = ProposalVote.by_hash(context["vote_hash"])

    if vote is None:
        raise ValidationError("Vote '%s' does not exist." % context["vote_hash"])
    
    method_name = vote.method_name
    
    if method_name not in vote_methods:
        raise ValidationError("Invalid voting method '%s'." % method_name)

    method = vote_methods[method_name]()

    ae = AExpr(method.vote_template, atypes)
    avars = ae.parse(tokens)
    method.checkAnswer(vote, **avars)
    return (method_name, avars)

def tMemberAccRejAbs(x):
    return ("member-vote-acc-rej-abs", {"answer" : tAccRejAbs(x)})

atypes = {
    "sha256" : tSHA256,
    "int" : tInt,
    "tokenlist" : tTokenList,
    "yesno" : tYesNo,
    "acc-rej-abs" : tAccRejAbs,
    "membername" : tMemberName,
    "address" : tAddress,
    "safestring" : tSafeString,
    
    "current_member"         : tCurrentMember,
    "votemaster"             : tVoteMaster,
    "votemethod"             : tVoteMethod,
    "voteanswer"             : tVoteAnswer,
    "member_acc_rej_abs"     : tMemberAccRejAbs
}
