from abc import ABCMeta, abstractmethod
from collections import Counter
import butypes
from jvalidate import ValidationError
from acheck import *

# Vote counting methods

class VoteMethod(metaclass=ABCMeta):
    spec_template = ""
    vote_template = ""
    
    def checkSpecification(self, **kwargs):
        pass
    
    def checkAnswer(self, vote, answer):
        pass

    @abstractmethod
    def summarize(self, result):
        pass # pragma: no cover

def answer_for_ballot(ballot):
    return ballot.parser.actvars["answer_tuple"][1]["answer"]
    
class BUIPARAVM(VoteMethod): # BUIP (A)ccept, (R)eject, (A)bstain vote method
    vote_template = "%answer:acc-rej-abs"


    def summarize(self, result):
        counts = {"accept" : 0, "reject" : 0, "abstain" : 0}

        for ballot in result.ballots:
            answer = answer_for_ballot(ballot)
            counts[answer]+=1
            
        accepts = counts["accept"]
        rejects = counts["reject"]
        abstains= counts["abstain"]

        # only count member eligible members
        Nmemb = sum(member.eligible()
                    for member in result.vote.action.member_list.members)
                
        quorum_reached = (accepts+rejects+abstains) >= 0.5 * Nmemb
        accepted = accepts>rejects and quorum_reached

        return {
            "accepts" : accepts,
            "rejects" : rejects,
            "abstains" : abstains,
            "quorum_reached" : quorum_reached,
            "accepted" : accepted}

class MemberARAVM(VoteMethod): # Accept, Reject, Abstain vote on members
    vote_template = "%answer:acc-rej-abs"


    def summarize(self, result):
        # FIXME: code dup with above
        
        counts = {"accept" : 0, "reject" : 0, "abstain" : 0}

        for ballot in result.ballots:
            answer = answer_for_ballot(ballot)
            counts[answer]+=1
            
        accepts = counts["accept"]
        rejects = counts["reject"]
        abstains= counts["abstain"]

        # only count member eligible members
        Nmemb = sum(member.eligible()
                    for member in result.action.member_list.members)
                
        quorum_reached = (accepts+rejects+abstains) >= 0.5 * Nmemb
        accepted = accepts>rejects and quorum_reached

        return {
            "accepts" : accepts,
            "rejects" : rejects,
            "abstains" : abstains,
            "quorum_reached" : quorum_reached,
            "accepted" : accepted}
    
vote_methods={
    # Regular BUIP YES/No vote
    # conditions:
    # majority of voters accept at least half of members are voting
    # OR:
    # 75% of voters accept with at least 25% of members voting
    "buip-acc-rej-abs" : BUIPARAVM,

    # member votes - same as BUIP?
    "member-vote-acc-rej-abs" : MemberARAVM
}
