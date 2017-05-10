#!/usr/bin/env python3
import datetime
import bitcoin
from sys import argv
import csv
from butype import *
from butypes import *
from appmaker import make_app

app, db=make_app(fresh=True)

bu_developer="theZerg"
bu_president="solex"
bu_secretary="Peter_R"

csv_file=open(argv[1], "r")

def date2epoch(s):
    if s == "never":
        return 0.0
    return datetime.datetime.strptime(s, "%d-%b-%y").timestamp()
    

entries = []
members = []
for row in csv.reader(csv_file):
    try:
        member_idx =int(row[0])

        nick = (row[1]
                .replace(" ", "_") # sorry ...
                )

        joined = date2epoch(row[3])
        app_text = row[4]

        addr = row[5]
        bitcoin.b58check_to_hex(addr)
        
        last_vote = date2epoch(row[6])

        last_action = max(joined, last_vote)

        print("Adding:", nick, addr)
        if 1:
            m = Member(nick, addr)
            Global.set_member_last_vote_time(m, last_action)
            members.append(m)
            db.session.add(m)
            db.session.commit()
            
        entries.append((nick, addr, last_action))
    except Exception as e:
        print ("Missing:", row[1])

if 1:
    developer=Member.by_name(bu_developer)
    president=Member.by_name(bu_president)
    secretary=Member.by_name(bu_secretary)

    print ("dev:", developer)
    print ("president:", president)
    print ("secretary:", secretary)

    ml = MemberList(
        members = members,
        secretary = secretary,
        president = president,
        developer = developer)

    Global.set_votemaster_rules(["secretary", "president"])
    
    db.session.add(ml)
    db.session.commit()
    Global.set_current_member_list(ml)
    db.session.commit()
    


