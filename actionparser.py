import re
import shlex

from actionexec import action_map
from atypes import atypes
from jvalidate import ValidationError
import aparser
from butype import db


class ActionParser:
    """ Parse an action and optionally execute it. """
    def __init__(self, action):
        self.action=action

        s=action.actstr.find(" ")
        act=action.actstr[:s]
        
        if act not in action_map:
            raise ValidationError("Unknown action '%s'." % act)
        self.act = act
        self.ae = action_map[act]()
        
        self.expr = aparser.AExpr(
            self.ae.template,
            atypes)
        self.actvars = self.expr(action.actstr[s+1:])
        
    def apply(self, upload, upload_data):
        C=action_map[self.act]
        d=self.actvars.copy()
        d.update({"upload" : upload,
                  "upload_data" : upload_data});

        res=self.ae.act(self.action, **d)
        db.session.add(self.action)
        return res
    
        
