from abc import abstractmethod
import os
import logging
import time
import json
import hashlib
from contextlib import contextmanager
import sqlalchemy.orm.exc
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm.session import make_transient

import config
import jvalidate

db=SQLAlchemy()

log=logging.getLogger(__name__)

def sha256(s):
    return hashlib.sha256(s).hexdigest()


# Mixin for all BU types
class BUType:
    def hashref(self):
        return self.x_sha256

    def xUpdate(self):
        self.x_json = (json.dumps(self.toJ(), sort_keys=True, indent=4)+"\n").encode("utf-8")
        hr=sha256(self.x_json)
        self.x_sha256 = hr

    def __str__(self):
        return "<BUobj %s, hash: %s...>" % (self.__tablename__, self.hashref()[:10])

    def serialize(self):
        return self.x_json
    
    def extraRender(self):
        return {
            "hashref" : self.hashref()
        }
    
    def public(self):
        return True

    @abstractmethod
    def dependencies(self):
        """ Retrieve immediately dependent objects, for zipping JSON stuff together. """
        pass # pragma: no cover

        
    # def unhinge(self):
    #     """ Clone this object and return it as a context manager. xUpdate() and add after
    #     context exit."""
    #     db.session.expunge(self)
    #     make_transient(self)
    #     self.id = None

    @classmethod
    def by_hash(cls, href):
        try:
            return cls.query.filter(cls.x_sha256 == href).one()
        except sqlalchemy.orm.exc.NoResultFound:
            return None
        
def defaultExtend(obj, j):
    j.update({
        "version" : 1,
        "type" : obj.__tablename__,
    })
    return j
