#!/bin/bash
cd `dirname $0`

while true; do
    date

    export LOG_DIR=~/buvlog
    mkdir -p $LOG_DIR

    test -f ready-to-start.flagfile && \
	echo "Starting gunicorn ..." && \
	~/.local/bin/gunicorn -w 8 --bind :9090 entry:app \
			      --access-logfile $LOG_DIR/access.log \
			      --error-logfile $LOG_DIR/error.log

    # reaching here? -> server has been killed. wait a bit to
    # not cause high-load loops in case something is seriously
    # wrong. A valid reason the server might have been killed is
    # a git push of new code.
    sleep 1
done
