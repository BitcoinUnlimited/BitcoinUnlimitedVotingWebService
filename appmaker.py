# appmaker: Create apps and DBs, both for real use and testing
import logging
import os
from flask_sqlalchemy import SQLAlchemy
from flask import Flask

import config
from butype import db

log=logging.getLogger(__name__)

def make_app(dbname=None, fresh=False):
    app = Flask("buv", static_url_path="")
    db_fn = dbname if dbname else config.database

    if fresh: # pragma: no cover
        try:
            ofn=db_fn.replace("sqlite:///", "")
            log.debug("Removing old DB: %s", ofn)
            os.remove(ofn)
        except:
            pass
        
    app.config["SQLALCHEMY_DATABASE_URI"] = db_fn
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True # necessary to trigger for hash recalc
    db.init_app(app)
    with app.app_context():
        db.create_all()
    app.app_context().push()
    return app, db


def make_test_app():
    app = Flask("buv")
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite://"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True # necessary to trigger for hash recalc
    db.init_app(app)
    with app.app_context():
        db.create_all()
    app.app_context().push()
    return app, db

    
