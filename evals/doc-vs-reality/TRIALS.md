# Trials: doc-vs-reality

House rule 8: tried in Claude Code (Haiku, Sonnet, Opus) and in Codex before `stable`.

| Agent | Eval cases | Triggers | State |
| :--- | :--- | :--- | :--- |
| Claude Code | 9 of 9 pass (3 cases x Haiku, Sonnet, Opus) | 12 of 12 (Haiku and Sonnet; 6 should, 6 near-miss) | done |
| Codex | 3 of 3 pass | not run | **pending** |

**Still needed before `stable`: a Codex pass.** At minimum one "should" trigger and one near-miss,
run in Codex with the skill installed. Then change `metadata.codex-check` in `SKILL.md` to `pass`
and `status` to `stable`.
