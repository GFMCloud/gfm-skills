# Database size
Type: task
Status: answered 2026-10-20
Blocked by: none

## Question
How big is the live database, and how long does a full dump take?

## Answer
9.1 GB; a full dump took 6 min 10 s. Evidence: `du -sh /var/lib/postgresql` gave 9.1G and
`time pg_dump shop > /dev/null` gave real 6m10s, run 2026-10-20 on the current server (demo values).
Unblocks: the cut-over window question.
