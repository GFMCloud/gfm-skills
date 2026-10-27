# Trials: automation

House rule 8: tried in Claude Code (Haiku, Sonnet, Opus) and in Codex before `stable`.

| Agent | Eval cases | Triggers | State |
| :--- | :--- | :--- | :--- |
| Claude Code | Opus 4 of 4 pass. Sonnet 3 of 3 pass on the current cases (plus the dropped in-session case, where it behaved right without the skill). Haiku nightly-backup, weekly-summary and overnight-loop pass; order-watch loaded the skill in 1 of 2 runs before the final fix (see below) | Haiku 4 of 4 should and 4 of 4 near-miss; Sonnet 4 of 4 should and 4 of 4 near-miss (one near-miss loaded proof-of-work, the intended neighbour) | done, with open items |
| Codex | not run | not run | **pending** |

Every run that loaded the skill wrote the job as files and installed, loaded or scheduled nothing.
Trial prompts carried an extra sentence forbidding scheduled tasks, cron, launchd, routines, loops
and hooks outside the workspace, so these trials can't show whether the skill alone would stop a
model from installing.

Changes during the trials: the loop shape was refocused on unattended loops, because on an
in-session "keep fixing until the tests pass" Haiku and Sonnet did the right thing without the skill
(the `fix-until-green` case was replaced by `overnight-loop`). An independent review found two
script bugs (non-UTF-8 input crashed `watch_state.py`; an unreadable guarded file released a Stop
hook) and a Haiku misreading ("install nothing" read as "schedule nothing"); all fixed, with
regression cases in `regress.sh`.

Helper scripts: `bash evals/automation/regress.sh` from the repo root (standard library only).

**Still needed before `stable`: a Codex pass.** At minimum `nightly-backup` (launchd job and proof
runs), `overnight-loop` (gate with `codex exec` as the agent step), one "should" trigger (the price
watch) and one near-miss (the backup-log question). Codex reads `SKILL.md` the same way, but the
runner reference's agent-step flags for `codex exec` were never run here. Then change
`metadata.codex-check` in `SKILL.md` to `pass` and `status` to `stable`.
