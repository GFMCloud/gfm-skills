# Trials: de-ai

House rule 8: tried in Claude Code (Haiku, Sonnet, Opus) and in Codex before `stable`.

| Agent | Eval cases | Triggers | State |
| :--- | :--- | :--- | :--- |
| Claude Code, first round | 8 pass, 1 partial (Haiku, `launch-post`: replaced a cut sentence with a new claim) | 6 of 6 should, 6 of 6 near-miss | done; fix applied |
| Claude Code, after the fix | Haiku `launch-post` passes, with the remaining rewording disclosed under `Kept:` | not rerun | done |
| Claude Code, after tightening `patterns.md` #15 | Haiku `launch-post` passes: no new claim; the missing link is left for the author | not rerun | done |
| Codex | not run | not run | **pending** |

Haiku tended to add a short linking sentence where an empty one was cut (also seen in trigger runs);
the third Haiku run, after the `patterns.md` fix, did not. Haiku sometimes leaves bold list labels.

**Still needed before `stable`: a Codex pass** (the `launch-post` case, one "should" trigger and one
near-miss). Then change `metadata.codex-check` in `SKILL.md` to `pass` and `status` to `stable`.
