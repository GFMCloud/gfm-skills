# Trials: retro

House rule 8: tried in Claude Code (Haiku, Sonnet, Opus) and in Codex before `stable`.

| Agent | Eval cases | Triggers | State |
| :--- | :--- | :--- | :--- |
| Claude Code, first build | 9 of 9 pass (3 cases x Haiku, Sonnet, Opus). All three models found the third occurrence and proposed a hook instead of a third rule | 6 of 6 should, 6 of 6 near-miss | done |
| Claude Code, "where to look" fold | 12 of 12 pass (6 cases x Sonnet, Opus), then 8 of 8 on reruns after the review fixes (6 Sonnet, 2 Opus). Both models found the unwired lint check from a plain prompt and kept an easy-to-reverse choice out of decision records | 6 of 6 should, 6 of 6 near-miss (Sonnet, full `triggers.yaml`) | done |
| Codex | not run | not run | **pending** |

Sonnet stands in for Haiku from the fold on.

**Still needed before `stable`: a Codex pass.** At minimum the `recurring-failure`, `lost-time` and
`unwired-check` cases, one "should" trigger and the "Which lines in my AGENTS.md don't change
anything?" near-miss (5 runs). Then change `metadata.codex-check` in `SKILL.md` to `pass` and
`status` to `stable`.
