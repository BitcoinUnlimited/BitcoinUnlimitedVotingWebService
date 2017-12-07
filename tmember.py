import time
import re
import logging
from sqlalchemy import LargeBinary, Integer, Float, String, Column, ForeignKey, Boolean
from sqlalchemy.orm import relationship
import sqlalchemy.orm.exc
from sqlalchemy.orm import load_only
from sqlalchemy import func
from jvalidate import ValidationError
from butype import *
from tglobal import Global
from atypes import tMemberName, tAddress
import config
from tmember_assoc import members_in_memberlists
from gpglayer import sanitize_pgppubkey

log=logging.getLogger(__name__)

sanitize_membername=tMemberName
sanitize_bitcoinaddr=tAddress

class Member(db.Model, BUType):
    """A BU member with name and Bitcoin address and memberlists s/he belongs to.
    """
    __tablename__="member"

    id = Column(Integer, primary_key=True)
    x_json = Column(LargeBinary, nullable=False)
    x_sha256 = Column(String(length=64), nullable=False, unique=True)

    # this is the most recent member object with the
    # given member_name
    # outdated member objects will have most_recent == False
    # the current flag is not part of the JSON string
    most_recent = Column(Boolean, nullable=False,
                     default=False)


    # no two members with same nick
    name = Column(String, nullable=False)

    # member's bitcoin address
    address = Column(String, nullable=False)

    # member's optional PGP public key
    pgp_pubkey = Column(String, nullable=True)

    # A member's optional member number
    # It is up to the vote master to manually
    # ensure that these values are unique.
    number = Column(Integer, nullable=True)

    # lists this member is part of
    member_lists = relationship("MemberList", secondary = members_in_memberlists,
                                back_populates="members")

    @classmethod
    def by_name(cls, name):
        """ Return most recent member object by giving member name. """
        try:
            return (cls.query.filter(cls.name  == name)
                    .filter(cls.most_recent).one())
        except sqlalchemy.orm.exc.NoResultFound:
            return None

    @classmethod
    def by_address(cls, address):
        """ Return most recent member object by giving member address. """
        try:
            return (cls.query.filter(cls.address  == address)
                    .filter(cls.most_recent).one())
        except sqlalchemy.orm.exc.NoResultFound:
            return None

    @classmethod
    def by_number(cls, number):
        """ Return most recent member by giving member's number.
        (Or None if nothing is found) """
        try:
            return (cls.query.filter(cls.number  == number)
                    .filter(cls.most_recent).one())
        except sqlalchemy.orm.exc.NoResultFound:
            return None

    def __init__(self,
                 name,
                 address,
                 pgp_pubkey = None,
                 number = None):
        """ Create a new, current member. If a current member with
        the given address or name exists already, fail. If
        the given member number is "assign-new", auto-assigned a non-used
        member number.
        """
        sanitize_membername(name)
        sanitize_bitcoinaddr(address)

        if pgp_pubkey is not None:
            sanitize_pgppubkey(pgp_pubkey)

        # Note: as-is, the member.number increment statement below is
        # subject to potential race conditions.
        # However, note also: all changes to the DB happen within the
        # write_lock as defined in serve.py, which should take care of
        # any races here. Note, though, that such an additional
        # locking scheme is needed.

        if number == "assign-new":
            old_max = db.session.query(func.max(Member.number)).one()[0]
            if old_max == None:
                number = 1
            else:
                number = old_max + 1

        if number is not None and number <= 0:
            raise ValidationError("Member number must be positive.")

        self.name = name
        self.address = address
        self.pgp_pubkey = pgp_pubkey
        self.number = number
        self.most_recent = True

        self.xUpdate()

    # helper value to be able to properly sort member lists using jinja2
    @property
    def number_or_zero(self):
        return self.number if self.number is not None else 0

    def toJ(self):
        d={
            "name" : self.name,
            "address" : self.address
        }
        if self.pgp_pubkey is not None:
            d["pgp_pubkey"] = self.pgp_pubkey

        if self.number is not None:
            d["number"] = self.number

        return defaultExtend(self, d)

    def dependencies(self):
        return []

    def last_vote_action(self):
        """ Returns the time (unix epoch) this member voted last. 0.0 if member never voted yet. """
        from taction import Action
        from tproposalvoteresult import ProposalVoteResult
        from tmemberelectionresult import MemberElectionResult

        last_action = (db.session
                   .query(func.max(Action.timestamp))
                   .join(Member)
                   .filter(Member.name == self.name))

        # last proposal vote
        last_pvote = (last_action
                      .filter(ProposalVoteResult.ballots.any(id=Action.id))
                      .one())[0]
        if last_pvote is None:
            last_pvote = 0.0

        # last member vote
        last_mvote = (last_action
                      .filter(MemberElectionResult.ballots.any(id=Action.id))
                      .one())[0]
        if last_mvote is None:
            last_mvote = 0.0

        return max(last_pvote, last_mvote)

    def last_member_confirmation(self):
        """Returns the time (unix epoch) this member was last voted on.
        The time a member is voted in is assumed to be the time of
        the last ballot cast on that particular vote. Returns 0.0 if the
        member was never confirmed (member existed before voting system).

        Note that a recent vote does not mean eligibility, as this
        does not check whether the vote was accepted by
        majority. Check the member list for that.
        """
        from taction import Action
        from tmemberelectionresult import MemberElectionResult

        q1 = (db.session
              .query(MemberElectionResult)
              .join(Member) # will join on MemberElectionResult.new_member
              .filter(Member.name == self.name))

        q2 = (db.session
              .query(func.max(Action.timestamp))
              .join(q1)
              .filter(MemberElectionResult.ballots.any(id=Action.id)))

        last_conf = q2.one()[0]

        return 0.0 if last_conf is None else last_conf

    def eligible(self):
        """Returns true iff member is eligible to vote.

        Remark:

        Note that the above two methods, last_member_confirmation()
        and last_vote_action() can NOT be used alone to determine member
        eligibility in all cases, as members who are on the initial member list
        will have an unknown time of last-vote from just the above
        queries.

        That's why a global configuration setting for those members
        will be used instead. In case a member has no configured external
        time of last vote and is not otherwise eligible, it is deemed
        not eligible to vote.

        """
        log.debug("Checking eligibility for: %s", self.name)
        if not self.current():
            log.debug("Not eligible, not a current member.")
            return False

        t=time.time()
        t_expire = t - config.member_expiry_time

        log.debug("Expiry time, relative to now:%f", t_expire - t)

        lva = self.last_vote_action()
        lmc = self.last_member_confirmation()

        log.debug("Last vote action relative to now:%f", lva - t)
        log.debug("Last member confirmation vote relative to now:%f", lmc - t)
        t_elig = max(lva, lmc)

        if t_elig > 0.0:
            # regular case: member has voted or been voted in
            eligible = t_elig > t_expire
            log.debug("Regular case eligibility check: %d", eligible)
            return eligible
        else:
            t_last = Global.member_last_vote_time(self)
            if t_last is None:
                log.debug("No last vote time for member set.")
            else:
                log.debug("Check from preset last vote date, relative to now: %f", t_last - t)
            if t_last is None:
                log.debug("Unknown preset last vote date -> not eligible")
                # member has unknown time of last vote -> not eligible
                return False
            else:
                eligible = Global.member_last_vote_time(self) > t_expire
                log.debug("Eligibility from config: %d", eligible)
                # member eligibility is determined from Global config
                return eligible

    def expiry_time(self):
        """ Return time when membership will expire. """

        # FIXME: some code dup with eligible() above
        t=time.time()
        lva = self.last_vote_action()
        lmc = self.last_member_confirmation()
        t_elig = max(lva, lmc)

        if t_elig > 0.0:
            # regular case: member has voted or been voted in
            return t_elig + config.member_expiry_time
        else:
            # member has a set expiry time
            t_last = Global.member_last_vote_time(self)
            if t_last is None:
                # expired - member has no expiry time set
                return 0.0
            else:
                return t_last + config.member_expiry_time


    def current(self):
        """ Is this member in current member list? """
        if Global.current_member_list() is not None:
            return self in Global.current_member_list().members
        else:
            return False
