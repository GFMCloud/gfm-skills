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
