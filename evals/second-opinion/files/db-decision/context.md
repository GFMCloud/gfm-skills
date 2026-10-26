# Context (demo material for an eval; the project is made up)

- A small booking app for a yoga studio. One server, about 40 bookings a day today.
- Data is in SQLite (one file, about 30 MB). Nightly backup copies the file.
- Launch to two more studios is planned in five weeks; expected load is about 150 bookings a day.
- One developer, part time. Has used Postgres before, not on this app.
- The hosting plan offers a managed Postgres add-on for a monthly fee.
- Two bugs last month were "database is locked" errors during the Sunday sign-up rush.
- The developer's current plan: move to Postgres now, before launch.
