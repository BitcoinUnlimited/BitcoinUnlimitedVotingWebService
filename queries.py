# functions to do various queries on the DB (search actions by members and so forth)

from butype import *
from butypes import *


def ActionByMemberNameAndType(
        membername,
        actiontype = None):
    """Return list of actions by type (or all if None) and member
name. Includes old actions by a member that has been superceded by a
member with the same nickname. Return sorted by most recent action first. """
    sel = list(
        db.session.query(Action)
        .join(db.session.query(Member)
              .filter(Member.name == membername))
        .order_by(Action.timestamp.desc()))

    if actiontype is None:
        return sel
    else:
        return [a for a in sel if a.actstr.startswith(actiontype+" ")]
    
