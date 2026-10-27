# Trials: decks

House rule 8: tried in Claude Code (Haiku, Sonnet, Opus) and in Codex before `stable`.

| Agent | Eval cases | Triggers | State |
| :--- | :--- | :--- | :--- |
| Claude Code | 9 of 9 pass (3 cases x Haiku, Sonnet, Opus). All three built decks start with the `Brand: project` line, pass `validate.py`, and draw only `data.csv` values | 6 of 6 should, 6 of 6 near-miss (the diagram went to `diagrams`, the chart to the built-in chart skill) | done |
| Codex | not run | not run | **pending** |

`validate.py --shots` needs Chromium through playwright. During these trials it failed inside the
sandbox on a macOS permission, and the runs re-ran that one step outside it. Fixed afterwards: the
validator now falls back to a single-process Chromium, which starts inside the sandbox (checked: the
example passes and a planted overflowing slide fails, both sandboxed). A missing or mismatched browser
now gets a one-line install command instead of a stack trace.

**Still needed before `stable`: a Codex pass.** At minimum the `build-branded` case, one "should"
trigger and one near-miss. Then change `metadata.codex-check` in `SKILL.md` to `pass` and `status`
to `stable`.

**2026-10-27, R12 real-task fixes (branch `fix/r12-trial-findings`):** SKILL.md text changed after
real-task trials on private projects (logs kept outside this repo). Earlier counts in this file
predate the change; rerun the triggers and cases before `stable`.
