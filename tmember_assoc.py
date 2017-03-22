from sqlalchemy import LargeBinary, Integer, Float, String, Column, ForeignKey, Boolean, Table
from butype import *

# Map members <-> memberlists
members_in_memberlists = Table("members_assoc", db.metadata,
                               Column("member_list_id", Integer, ForeignKey("member_list.id")),
                               Column("member_id", Integer, ForeignKey("member.id")))
