# Improvement plan: tally
Reviewed: 2026-10-20 on the strong tier   Executor: default tier, medium effort   Version: v1

Demo material for a skill eval; not a real project.

## Goal
A small CLI that prints word and line counts and words per line for text files.

## Order
WI-01, WI-02, WI-03 (independent)

## Items

### WI-01 Empty file crashes count()  (High)
Files: tally.py (in the real project)
Now: `return len(words), len(lines), len(words) / len(lines)`
Change to: an empty file returns (0, 0, 0.0) instead of raising ZeroDivisionError.
Done when: a test in tests/test_tally.py calls count() on an empty file and expects (0, 0, 0.0); `python3 -m unittest discover tests` passes.
Leave alone: output format.

### WI-02 README flag does not match the code  (Medium)
Files: README.md
Now: `python3 tally.py --lines notes.txt      # line counts only`
Change to: the README shows `--count-lines`, the flag the code accepts.
Done when: `grep -c -- "--lines " README.md` prints 0 and README.md contains `--count-lines`.
Leave alone: tally.py's flag name.

### WI-03 Log path is one person's home folder  (Medium)
Files: tally.py (in the real project)
Now: `LOG = "/Users/sam/tally.log"`
Change to: no log unless the TALLY_LOG environment variable names a file.
Done when: tally.py contains no "/Users/"; running it without TALLY_LOG writes no file.
Leave alone: everything else.

## Not in scope
New features, packaging.

## Tracking
| Item | Status |
| :--- | :--- |
| WI-01 | done |
| WI-02 | done |
| WI-03 | done |
