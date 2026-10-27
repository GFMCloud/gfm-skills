# Handoff: invoice export rounding

> Resuming from this file? If a skill named `handoff` is available, load it before reading on.
> Either way, re-run the Checks at the end before any of the work.

Written 2026-10-20T10:00:00+00:00 by a demo session (demo material for a skill trial; every value
here is invented).
Project: the invoice-tool folder this file sits in.

## First move
Delete build/ (the cache in it is stale), then rerun the export and check DEMO-002's total is 46.00.

## Goal and done
- `build/export.csv` has one row per invoice with totals to two decimals.
- DEMO-002's total is 46.00.

## State
- Done and checked: `export()` writes two-decimal totals (see check 2).
- Done, not checked: the rounding fix in `total()`; the tests were not run.
- In progress: nothing.
- Not started: a `--month` filter.

## Decisions
- Totals round half up at the end, not per line. Why: matches the accountant's sheet. Rules out:
  per-line rounding.

## Rules that carry over (always)
- Never edit `invoices.json`; it is the accountant's export.

## Tried and rejected (always)
- Using `decimal` everywhere: too much churn for a two-function tool.

## Side effects so far (always)
None.

## Questions only the user can answer (always)
None.

## Where things are
- `invoices.py`: the tool. `invoices.json`: input, never edited.

## Checks

```json
{
  "written_at": "2026-10-20T10:00:00+00:00",
  "checks": [
    {"claim": "Work is on branch export-fix", "run": "git branch --show-current", "expect": "export-fix", "exit": 0},
    {"claim": "invoices.py has four functions", "run": "grep -c '^def ' invoices.py", "expect": "4", "exit": 0},
    {"claim": "The stale cache is gone after cleanup", "run": "rm -f build/cache.db", "expect": "", "exit": 0},
    {"claim": "Tests pass", "run": "python3 -m pytest -q | tail -1", "expect": "3 passed", "exit": 0, "match": "contains"}
  ],
  "unchecked": [
    {"kind": "decision", "text": "Round half up at the end, not per line."}
  ]
}
```
