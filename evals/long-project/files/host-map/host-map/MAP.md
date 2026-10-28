# Map: host move (demo material)

## Destination
A written choice of new host for the shop app, with the region and the cut-over window agreed,
ready to hand to a phased move project.

## Notes
- The shop owner answers grill questions; research answers need dated sources.

## Decisions so far
- Database size: 9.1 GB, a full dump takes about 6 minutes (questions/database-size.md)

## Not yet specified
- Whether backups must stay in the same region as the live data (waits on the region question).
- How customer photo uploads are stored on the new host (waits on the host choice).

## Out of scope
- Rewriting the app or changing its database engine: a separate effort.
