#!/usr/bin/env python3
import logging
logging.basicConfig(level=logging.DEBUG)
import sys
import argparse
import serve
import butypes

def buvcmd():
    parser=argparse.ArgumentParser(description="Bitcoin Unlimited Voting backend")

    subparsers=parser.add_subparsers()

    # start micro web service
    serve_parser=subparsers.add_parser("webserver", help="Start micro web service")
    serve_parser.set_defaults(func=serve.serve)

    args=parser.parse_args()

    if "func" in args:
        args.func()
    else:
        raise RuntimeError("No sub argument given.")


if __name__=="__main__": # pragma: no cover
    buvcmd()
