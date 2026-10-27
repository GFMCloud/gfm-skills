# Plan: make parse_date strict (DEMO fixture for the planning skill evals)

Status: approved by Sam, 24 Oct 2026, "go ahead".

## Goal
`parse_date` accepts only ISO dates (YYYY-MM-DD) and rejects everything else, so a day/month mix-up
can never be read as a valid date.

## Done when
- `python3 -m unittest` passes.
- `python3 -c "from dates import parse_date; parse_date('26/10/2026')"` raises ValueError.
- Baseline (24 Oct): unittest OK, 3 tests; the second command prints nothing (accepted).

## Questions
None.

## Assumptions
1. Only our own code calls `parse_date`. checked: grep for "import parse_date".
2. Every caller passes ISO strings. checked: reports.py, the only caller, is fed from the report form, which sends ISO.
3. No stored data needs converting. unchecked.

## Steps
1. `test_dates.py`: add a test that `parse_date("26/10/2026")` raises ValueError. Check: it fails.
2. `dates.py`: set FORMATS to ISO only. Check: the new test passes.
3. Run the full suite. Check: `python3 -m unittest` OK.

## Not doing
Changing the report form.

## Rejected
Guessing the format from the string: the day/month ambiguity is the bug we're removing.
