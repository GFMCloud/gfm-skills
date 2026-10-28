# Session log (demo material for an eval; the project is made up)

Project: a small online shop for a pottery studio. Session ran 09:00 to 10:40.

09:05 User: customers can guess other people's order URLs (/orders/1041, /orders/1042).
09:15 Agent compared options for public order IDs: keep integers and add an auth check only; random
      UUIDv4; time-ordered UUIDv7. Trade-off: UUIDv7 keeps index order and hides the count, but every
      order URL already sent in confirmation emails must keep working, so old integer URLs need a
      redirect table kept forever. User chose UUIDv7 plus the redirect table.
09:50 Commit 5e6f7a8 "Public order IDs as UUIDv7; redirect old integer URLs".
10:00 Agent asked whether the new ID helper goes in shop/ids.py or shop/utils/ids.py. User: "either,
      put it in shop/ids.py".
10:10 Agent wrote the new tests with pytest, like the rest of the suite.
10:25 User set pytest's per-test timeout to 5 s in pytest.ini (it had none), because the CI runner
      kills the whole job at 10 minutes and one hung test had eaten a full run. Trade-off: a slow but
      correct test now fails. It is one line to change back.
10:35 Commit 9a0b1c2 "Move ID helper to shop/ids.py; add tests".
