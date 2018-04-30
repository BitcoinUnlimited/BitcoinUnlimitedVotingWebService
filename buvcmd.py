#!/usr/bin/env python3
import logging
logging.basicConfig(level=logging.DEBUG)
import sys
import argparse
import serve
import butypes
import member_helpers

def buvcmd():
    parser=argparse.ArgumentParser(description="Bitcoin Unlimited Voting backend")

    subparsers=parser.add_subparsers()

    # start micro web service
    serve_parser=subparsers.add_parser("webserver", help="Start micro web service")
    serve_parser.set_defaults(func=serve.serve)

    # update a member's data
    # Note: the web service should be switched off for this, due to the (very) small
    # risk of database access races.
    serve_update_member = subparsers.add_parser("update-member", help="Update a member's data")
    serve_update_member.add_argument("name", type=str, help="Name of member to change.")
    serve_update_member.add_argument("--address", "-a", type=str, help="Set a member's Bitcoin address.")
    serve_update_member.add_argument("--pgp_key_file", "-p", type=str, help="Set a member's PGP key from a file.")
    serve_update_member.add_argument("--number", "-n", type=int, help="Set a member's number.")
    serve_update_member.set_defaults(func=member_helpers.update_member_cmd)


    # add a member
    # Note: the web service should be switched off for this, due to the (very) small
    # risk of database access races.
    serve_add_member = subparsers.add_parser("add-member", help="Add a member to the current member list")
    serve_add_member.add_argument("name", type=str, help="Name of new member.")
    serve_add_member.add_argument("address", type=str, help="Bitcoin address of new member.")
    serve_add_member.add_argument("number", type=int, help="Set a member's number.")
    serve_add_member.add_argument("last_vote_time", type=str, help="Last vote time of member in format d-m-YYYY.")
    serve_add_member.add_argument("--pgp_key_file", "-p", type=str, help="PGP key of new member.")
    serve_add_member.set_defaults(func=member_helpers.add_member_cmd)

    # set member's last vote time special entry
    serve_set_member_last_vote_time = subparsers.add_parser("set-last-vote-time", help="Sets a member's last voting time override manually")
    serve_set_member_last_vote_time.add_argument("name", type=str, help="Member name.")
    serve_set_member_last_vote_time.add_argument("last_vote_time", type=str, help="Last vote time of member to set in format d-m-YYYY.")
    serve_set_member_last_vote_time.set_defaults(func=member_helpers.set_member_last_vote_time)

    args=parser.parse_args()

    if "func" in args:
        args.func(args)
    else:
        raise RuntimeError("No sub argument given.")


if __name__=="__main__": # pragma: no cover
    buvcmd()
