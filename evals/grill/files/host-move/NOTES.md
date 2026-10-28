# Moving the app off the old VPS (DEMO FIXTURE, not a real project)

The bakery order app runs on one rented VPS that we patch by hand. I want it on a managed host
before the busy season so nobody has to babysit a server.

What I know so far:
- It's a Node app with a Postgres database.
- There's only one cron job, the nightly backup.
- Customers upload photos for custom cake orders.
- The domain is orders.example-bakery.test, DNS at the registrar.

Not sure yet: which host, whether the database moves too, how much downtime is OK.
