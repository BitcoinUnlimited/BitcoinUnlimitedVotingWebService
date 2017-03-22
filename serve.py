# Web front end
import os
import logging
from flask import (Flask, render_template, send_from_directory,
                   abort, Response, request, jsonify)

from flask_sqlalchemy import SQLAlchemy
from flask_basicauth import BasicAuth
import sqlalchemy.exc
import config
import butype
import butypes
import urlvalidate
import jvalidate
import appmaker
from butypes import *

log=logging.getLogger(__name__)

def make_app(test_mode_internal=False):
    if test_mode_internal:
        app, db=appmaker.make_test_app()
    else: # pragma: no cover
        app, db=appmaker.make_app()
    
    app.config['TEMPLATES_AUTO_RELOAD'] = True

    if 0:
        app.config['BASIC_AUTH_USERNAME'] = 'unlimited'
        app.config['BASIC_AUTH_PASSWORD'] = 'voting'
        app.config['BASIC_AUTH_FORCE'] = True
        basic_auth = BasicAuth(app)

    urlvalidate.register(app)

    app.jinja_env.globals["web_root"]=config.web_root
    app.jinja_env.globals["action_prefix"]=config.action_prefix

    @app.route('/api1/js/<path:path>')
    def js_static(path):
        return send_from_directory('js', path)

    @app.route("/api1/")
    def _entry():
        cml = Global.current_member_list()

        published = cml.proposals().filter(ProposalMetadata.file_public == True)
        member_applications = cml.applications()
        return render_template("index.html",
                               proposals = published,
                               member_applications = member_applications,
                               cml = cml)

    @app.route("/api1/unpublished-proposals")
    def _unpublished():
        unpublished_proposals = (
            Global
            .current_member_list()
            .proposals()
            .filter(ProposalMetadata.file_public == False))
        return render_template("unpublished_proposals.html",
                               proposals = unpublished_proposals)

    @app.route("/api1/debug")
    def get_debug_overview():
        if config.test_mode:
            return render_template("debug_overview.html")
        else:
            abort(404)

    @app.route("/api1/debug/objects")
    def _get_debug_objects():
        if config.test_mode:
            objmap=get_all_objects()
            return render_template("debug_objects.html",
                           objmap = objmap)
        else:
            abort(404)

    @app.route("/api1/debug/current-member-list-hash")
    def _get_debug_current_member_list_hash():
        if not config.test_mode:
            abort(404)
        return Global.current_member_list().hashref()

    @app.route("/api1/debug/meta-for-raw-file/<shex:hashval>")
    def _get_debug_meta_for_raw(hashval):
        if not config.test_mode:
            abort(404)
            
        obj = RawFile.by_hash(hashval)
        if obj is None:
            abort(404)
        else:
            return obj.proposal_metadata.hashref()

    @app.route("/api1/debug/vote-for-raw-file/<shex:hashval>")
    def _get_debug_vote_for_raw_file(hashval):
        if not config.test_mode:
            abort(404)

        v= ProposalVote.by_raw_file_hash(hashval)
        if v is None:
            abort(404)
        else:
            return v.hashref()

    @app.route("/api1/debug/result-for-vote/<shex:hashval>")
    def _get_debug_result_for_vote(hashval):
        if not config.test_mode:
            abort(404)

        v=ProposalVote.by_hash(hashval)
        if v is None:
            abort(404)
        else:
            return v.result.hashref()

    @app.route("/api1/debug/summary-of-proposal-vote-result/<shex:hashval>")
    def _get_debug_summary_of_proposal_vote_result(hashval):
        if not config.test_mode:
            abort(404)

        v=ProposalVoteResult.by_hash(hashval)
        if v is None:
            abort(404)
        else:
            return jsonify(v.summarize())
        
    @app.route("/api1/debug/testkeys")
    def get_testkeys():
        if config.test_mode:
            from test_tmemberlist import makeTestMemberKeys

            testmembers = makeTestMemberKeys()

            return render_template("debug_testkeys.html",
                           testmembers = zip(*testmembers))
        else:
            abort(404)

    @app.route("/api1/render/<objtype:name>/<shex:hashval>")
    def _render(name, hashval):
        Cls = name2type[name]
        obj=Cls.by_hash(hashval)

        if obj is None:
            abort(404)

        if not obj.public():
            abort(401) # FIXME: or simply 404?

        try:
            j=obj.toJ()
        except RuntimeError:
            abort(404) # no JSON representation possible -> can't be rendered


        v=obj.extraRender()
        v.update({name : obj })

        return render_template("render_%s.html" % obj.__tablename__,
                               render_object_type = name,
                               render_object_id = hashval,
                               **v)


    @app.route("/api1/raw/<objtype:name>/<shex:hashval>")
    def _get_raw(name, hashval):
        Cls = name2type[name]
        obj=Cls.by_hash(hashval)

        if obj is None:
            abort(404)
        if not obj.public():
            abort(401)

        if isinstance(obj, butypes.RawFile):
            return Response(response=obj.data,
                            mimetype=obj.proposal_metadata.mime_type,
                            headers=
                            {
                                "Content-Disposition":
                                "attachment;filename=%s" % obj.proposal_metadata.filename
                            })
        else:
            return Response(response=obj.x_json, mimetype = "application/json")

    @app.route("/api1/form/<name>")
    @app.route("/api1/form/<name>/<shex:hashval>")
    def _form(name, hashval=None):
        if name not in [
                "generic", "proposal-upload", "proposal-publish",

                "open-proposal-vote", "close-proposal-vote",
                "cast-proposal-ballot",
                "propose-member"]:
            abort(404)

        return render_template(
            "form_"+name+".html",
            cml = Global.current_member_list(),
            hashval = hashval)

    @app.route("/api1/form/cast-member-ballot/<name>/<address>")
    def _form_cast_member_ballot(name, address):
        return render_template(
            "form_cast-member-ballot.html",
            cml = Global.current_member_list(),
            member_name=name,
            member_address=address)

    @app.route("/api1/form/close-member-elections")
    def _form_close_member_elections():
        cml = Global.current_member_list()
        ma_names = " ".join(ma.new_member.name for ma in cml.applications())
        return render_template(
            "form_close-member-elections.html",
            cml = cml,
            ma_names = ma_names)



    @app.route("/api1/action", methods=["POST"])
    def _action():
        author_name = request.form["author_name"] if "author_name" in request.form else None
        action_string = request.form["action_string"] if "action_string" in request.form else None
        signature = request.form["signature"] if "signature" in request.form else None

        upload    =request.files["upload"] if "upload" in request.files else None

        log.debug("action: Extracted fields")

        if author_name is None:
            abort(403, "Author name field is missing.")
        if action_string is None:
            abort(403, "Action string is missing.")
        if signature is None:
            abort(403, "Signature is missing.")

        author = Member.by_name(author_name)

        if author is None:
            abort(403, "Author '%s' does not exist." % author_name)

        if upload is not None:
            data=upload.read(config.max_upload+1)
            if len(data)>config.max_upload:
                abort(413, "Upload too large.")

            hash_ref=butype.sha256(data)
            log.debug("Upload data hash: %s, len: %d", hash_ref, len(data))

            if RawFile.by_hash(hash_ref) is not None:
                abort(409, "File exists.")

        else:
            hash_ref=None
            data=None
        log.debug("action: Handled upload")

        try:
            action=butypes.Action(#timestamp=None,
                                    author=author,
                                    action_string=action_string,
                                    signature=signature)
            returnval=action.apply(upload, data)
        except jvalidate.ValidationError as ve:
            log.warn("Action: Problem: %d, %s", ve.status, str(ve))
            abort(ve.status, str(ve))

        try:
            db.session.commit()
        except sqlalchemy.exc.IntegrityError as ie: # pragma: no cover
            # should not happen, but better be prepared
            log.warn("SQLalchemy integrity error: %s", ie)
            abort(403, "Database integrity error.")

        log.debug("action: Successful execution")
        return render_template("on_action_%s.html" % action.parser.act,
                               action = action,
                               returnval = returnval), 201

    @app.route("/api1/zip/<objtype:name>/<shex:hashval>")
    def _get_zip(name, hashval):
        import io
        import zipfile

        Cls = name2type[name]
        obj=Cls.by_hash(hashval)

        if obj is None:
            abort(404)
        if not obj.public():
            abort(401)

        output = io.BytesIO()

        with zipfile.ZipFile(file=output, mode="w", compression=zipfile.ZIP_DEFLATED) as zip:

            already = set()
            def writeObjAndDeps(obj, level):
                log.debug("Writing object: %d %s", level, obj)
                if obj.public() and obj not in already:
                    if obj.__tablename__ != RawFile.__tablename__:
                        zip.writestr(
                            os.path.join("buv-export", obj.__tablename__,
                                         obj.hashref()+".json"), obj.serialize())
                    else:
                        zip.writestr(
                            os.path.join("buv-export", obj.__tablename__,
                                         obj.hashref()+".file"), obj.serialize())

                    already.add(obj)
                    for dep in obj.dependencies():
                        writeObjAndDeps(dep, level+1)

            writeObjAndDeps(obj, 0)

        mime_type = "application/zip"
        return Response(response=bytes(output.getbuffer()),
                            mimetype=mime_type,
                            headers=
                            {
                                "Content-Disposition":
                                "attachment;filename=%s" % obj.__tablename__+"-"+obj.hashref()+".zip"
                            })
    return app, db

def serve(): # pragma: no cover
    app, db = make_app()
    print("Starting buv web server on localhost:9090.")
    app.run(host='localhost', port=9090, debug=config.debug_mode)
    
