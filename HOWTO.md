# How to set 'last vote override time' for those members that do not use the voting system consistently

On the voting server, stop the `gunicorn` app server instances by
(as user awemany) removing the file `ready-to-start.flagfile` and
then attaching to the screen session with `screen -r` and entering
a `ctrl-C` there. Check with `ps aux` that there is no instance left
running.

After this (and now is a good time to do a backup of the DB db.sqlite...!),
a member's last voting time can be set like this:

$ ./buvcmd.py set-last-vote-time VeritasSapere 12-12-2017
DEBUG:tglobal:global set member_last_vote_time_VeritasSapere=1513036800.0



