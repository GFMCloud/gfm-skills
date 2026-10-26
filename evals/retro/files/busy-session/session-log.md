# Session log (demo material for an eval; the project is made up)

Project: a small invoicing web app. Session ran 09:10 to 11:40.

09:12 User: the monthly report test fails on CI but passes on my laptop.
09:20 Agent ran `pytest tests/test_report.py` locally: 12 passed.
09:31 Agent read the CI log: `AssertionError: expected 2026-03-31, got 2026-04-01` in test_month_end.
09:45 Agent found that `report.month_end()` uses `datetime.now()` (local time). CI runs in UTC; the
      laptop is UTC-5. Late-evening runs cross midnight in UTC.
10:05 Agent changed `month_end()` to take a timezone-aware `now` argument and fixed the test to pass
      a fixed time. All 14 tests pass locally and on CI.
10:07 Commit a1b2c3d "Make month_end timezone-aware; pin the test clock".
10:20 User asked whether to store invoice PDFs in the database or on disk.
10:25 Agent compared: database (simpler backups, bigger DB) and disk (smaller DB, a second thing to
      back up). User chose disk with paths in the database, "because the DB is already 2 GB".
10:40 Agent wrote that decision into a comment in storage.py only.
11:00 Agent spent 20 minutes on a lint error that turned out to be a typo in a variable name.
11:38 Commit d4e5f6a "Store invoice PDFs on disk; keep paths in the invoices table".
