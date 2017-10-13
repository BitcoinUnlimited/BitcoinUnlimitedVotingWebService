#!/bin/bash
# Variant of the start-server.sh script solely meant for testing
# This one will start gunicorn on :9595 (the testing port)
# Push to the live-testing branch on the vote server for
# updating the testing configuration.

cd `dirname $0`

while true; do
    date

    export LOG_DIR=~/buvlog-testing
    mkdir -p $LOG_DIR

    test -f ready-to-start.flagfile && \
	echo "Starting gunicorn ..." && \
	~/.local/bin/gunicorn -w 8 --bind :9595 entry:app \
			      --access-logfile $LOG_DIR/access.log \
			      --error-logfile $LOG_DIR/error.log \
			      --preload \
			      --access-logformat '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(p)s %(D)s'

    # reaching here? -> server has been killed. wait a bit to
    # not cause high-load loops in case something is seriously
    # wrong. A valid reason the server might have been killed is
    # a git push of new code.
    sleep 1
done
