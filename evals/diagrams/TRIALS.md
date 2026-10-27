# Trials: diagrams

House rule 8: tried in Claude Code (Haiku, Sonnet, Opus) and in Codex before `stable`.

| Agent | Eval cases | Triggers | State |
| :--- | :--- | :--- | :--- |
| Claude Code, first round | 6 pass, 3 partial (all missed the `Brand:` first line) | 5 of 6 should (Haiku missed "data pipeline"), 9 of 9 near-miss | done; fixes applied |
| Claude Code, after fixes | the 3 former partials now pass (Haiku x2, Opus) | Haiku still asks before loading for "data pipeline" in an empty folder | done |
| Codex | 2 of 2 pass (three-tier-app, project-brand); vague-request not run | not run | **pending** |

**Still needed before `stable`: a Codex pass.** At minimum the vague-request case, one "should"
trigger and one near-miss, run in Codex with the skill installed. Then change
`metadata.codex-check` in `SKILL.md` to `pass` and `status` to `stable`.

**2026-10-27, R12 real-task fixes (branch `fix/r12-trial-findings`):** SKILL.md text changed after
real-task trials on private projects (logs kept outside this repo). Earlier counts in this file
predate the change; rerun the triggers and cases before `stable`.
