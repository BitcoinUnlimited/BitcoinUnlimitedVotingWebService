# actionexec: Execute actions on voting system
# Any changes to the DB should be done by functions defined herein.

from abc import ABCMeta, abstractmethod
import os
import werkzeug

import config
from acheck import *
from butypes import *
from butype import db
from jvalidate import ValidationError, is_sha256

class ActionExec(metaclass=ABCMeta):
    template = ""
    @abstractmethod
    def act(self, action, upload, upload_data, **kwargs):
        pass # pragma: no cover

class ProposalUploadAE(ActionExec):
    template = "file %file_hash:sha256 by %member:current_member"
    def act(self, action, upload, upload_data, file_hash, member):
        checkAuthor(action, member)
        checkUpload(upload, upload_data)

        fobj=RawFile(upload_data)

        if fobj.hashref() != file_hash:
            raise ValidationError(
                "Uploaded data has hash %s but expected %s as in action." %
                (fobj.hashref(), file_hash))

        mobj=ProposalMetadata(
            filename=werkzeug.secure_filename(upload.filename),
            mime_type=upload.content_type,
            raw_file=fobj,
            action=action)

        fobj.proposal_metadata = mobj
        db.session.add(fobj)
        db.session.add(mobj)

class ProposalPublishAE(ActionExec):
    template = "file %file_hash:sha256 by %member:votemaster"
    def act(self,
            action,
            upload,
            upload_data,
            file_hash,
            member):
        checkAuthor(action, member)
        checkNoUpload(upload, upload_data)

        fobj = RawFile.by_hash(file_hash)

        if fobj is None:
            raise ValidationError("File to publish does not exist.")

        mobj = fobj.proposal_metadata
        if mobj is None:
            raise ValidationError("File needs to have metadata.")

        if fobj.public():
            raise ValidationError("File is already public.")

        nmobj= ProposalMetadata(
            filename=mobj.filename,
            mime_type=mobj.mime_type,
            raw_file=fobj,
            action=mobj.action,
            file_public=True)

        fobj.proposal_metadata = nmobj

        db.session.delete(mobj)
        db.session.add(nmobj)

class OpenProposalVoteAE(ActionExec):
    template = "meta %meta_hash:sha256 by %member:votemaster method (method:votemethod)"
    def act(self, action, upload, upload_data, meta_hash, member, method):
        method_name, method_options = method
        checkAuthor(action, member)
        checkNoUpload(upload, upload_data)

        mobj = ProposalMetadata.by_hash(meta_hash)
        if mobj is None:
            raise ValidationError("Proposal metadata '%s' does not exist." % meta_hash)

        if not mobj.file_public:
            raise ValidationError("Proposal needs  to be published first.")
        
        fobj = mobj.raw_file

        if mobj.vote is not None:
            raise ValidationError("Vote already open for object '%s'/'%s'." % (fobj, mobj))

        with db.session.no_autoflush:
            vobj = ProposalVote(fobj, mobj, action, method_name, method_options)
            robj = ProposalVoteResult(vobj)
        db.session.add(vobj)
        db.session.add(robj)

        return vobj

class CloseProposalVoteAE(ActionExec):
    template = "result %result_hash:sha256 by %member:votemaster"
    def act(self, action, upload, upload_data, member, result_hash):
        checkAuthor(action, member)
        checkNoUpload(upload, upload_data)

        result = ProposalVoteResult.by_hash(result_hash)
        if result is None:
            raise ValidationError("Proposal result '%s' does not exist." % result_hash)

        if not result.is_open:
            raise ValidationError("Result is already closed.")
        result.close()
    
class CastProposalBallotAE(ActionExec):
    template = "vote %vote_hash:sha256 by %member:current_member answer (answer_tuple:voteanswer)"
    def act(self, action, upload, upload_data, vote_hash, member, answer_tuple):
        from vote_methods import vote_methods

        method_name, answer = answer_tuple

        checkAuthor(action, member)
        checkNoUpload(upload, upload_data)

        vote = ProposalVote.by_hash(vote_hash)

        if vote is None: # pragma: no cover
            # should not happen as voteanswer type check checks that vote_hash is valid implicitly
            raise ValidationError("Vote '%s' does not exist." % vote_hash)

        if vote.result is None: # pragma: no cover
            # should never happen as all proposal votes are created
            # with result object attached and SQLAlchemy should check this
            raise ValidationError("Vote result does not exist.")
        vote.result.cast(action, method_name, answer)

class ProposeMemberAE(ActionExec):
    template = "name %name:membername address %address:address by %member:votemaster"
    def act(self, action, upload, upload_data, name, address, member):
        checkAuthor(action, member)
        checkNoUpload(upload, upload_data)

        with db.session.no_autoflush:
            if Member.by_name(name) is not None:
                raise ValidationError("Member '%s' exists already." % name)
            
            if Member.by_address(address) is not None:
                raise ValidationError("Member '%s' already uses address '%s'." %
                                      (Member.by_address(address).name, address))
                    
            m = Member(name = name,
                       address = address)

            nme = MemberElectionResult(m, action)

        db.session.add(m)
        db.session.add(nme)

class CastMemberBallotAE(ActionExec):
    template = "name %name:membername address %address:address by %member:current_member answer %answer_tuple:member_acc_rej_abs"
    
    def act(self, action, upload, upload_data, name, address, member, answer_tuple):
        method_name, answer = answer_tuple

        checkAuthor(action, member)
        checkNoUpload(upload, upload_data)

        member = Member.by_name(name)
        if member.address != address:
            raise ValidationError("Address '%s' for new member '%s' different from expected '%s'." %
                                  (address, name, member.address))
        
        election = MemberElectionResult.by_member(member)

        if election is None:
            raise ValidationError("No election for member '%s' exists." % member.name)

        election.cast(action, method_name, answer)

class CloseMemberElectionsAE(ActionExec):
    template = "all [names:membername] by %member:votemaster" # make it explict
    
    def act(self, action, upload, upload_data, names, member):
        checkAuthor(action, member)
        checkNoUpload(upload, upload_data)

        ml = Global.current_member_list()
        mers = ml.applications()

        names = set(names)
        app_names=set(a.new_member.name for a in mers)

        if app_names != names:
            raise ValidationError("Currently, all new member elections must be closed at once.")

        new_members=[r.new_member for r in mers if r.summarize()["accepted"]]

        new_memberlist=MemberList(
            members = ml.members+new_members,
            secretary = ml.secretary,
            president = ml.president,
            developer = ml.developer,
            previous = ml)

        for mer in mers:
            mer.close()
            
        db.session.add(new_memberlist)
        db.session.commit()
        Global.set_current_member_list(new_memberlist)
        
action_map={
    "proposal-upload" : ProposalUploadAE,
    "proposal-publish" : ProposalPublishAE,

    "open-proposal-vote" : OpenProposalVoteAE,
    "close-proposal-vote" : CloseProposalVoteAE,
    "cast-proposal-ballot" : CastProposalBallotAE,

    "propose-member" : ProposeMemberAE,
    "cast-member-ballot" : CastMemberBallotAE,
    "close-member-elections" : CloseMemberElectionsAE
}
