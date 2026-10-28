# Plan: CSV export of invoices (DEMO fixture for the planning skill evals)

Status: approved by Sam, 26 Oct 2026, "go ahead".

## Goal
`export_csv(invoices, path)` in invoice.py writes one row per invoice, with a header row, so the
bookkeeper can open the month's invoices in a spreadsheet.

## Done when
- `python3 -m unittest` passes, including a new export test.
- Test seam: `export_csv`, called the way the bookkeeper's script will call it.
- Baseline (26 Oct): unittest OK, 2 tests.

## Questions
None.

## Assumptions
1. An invoice is a dict with `number`, `date`, `lines` and an optional `code`. decided: Sam, 26 Oct 2026.
2. Totals in the export come from the existing `total()`. decided: Sam, 26 Oct 2026.
3. No new dependencies: the standard `csv` module only. checked: invoice.py imports nothing else.

## Steps
1. `test_invoice.py`: add `test_export_csv`, which exports two invoices to a temporary file and checks
   the header `number,date,subtotal,code,total` and both rows. Check: it fails (no `export_csv` yet).
   blocked by: none
2. `invoice.py`: add `export_csv(invoices, path)` writing those five columns with the `csv` module.
   Check: the new test passes. blocked by: 1
3. Run the full suite. Check: `python3 -m unittest` OK, 3 tests. blocked by: 2

## Not doing
The WELCOME10 discount bug (codes are taken off as money, not a percentage): a separate fix with its
own plan.

## Rejected
pandas: a new dependency for five columns.
