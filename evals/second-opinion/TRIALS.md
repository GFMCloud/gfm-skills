# Trials: second-opinion

House rule 8: tried in Claude Code (Haiku, Sonnet, Opus) and in Codex before `stable`.

| Agent | Eval cases | Triggers | State |
| :--- | :--- | :--- | :--- |
| Claude Code | 9 of 9 pass (3 cases x Haiku, Sonnet, Opus). The first wording of `announcement-check` went to `doc-vs-reality`; the prompt now asks for independent reviewers and the skill names the boundary | 5 of 6 should (Haiku answered "are you just agreeing?" without the skill, following the test machine's own instructions), 6 of 6 near-miss | done |
| Codex | not run | not run | **pending** |

Subagents could start subagents in these runs, so the voices and reviewers were real fresh contexts,
mostly on a different model from the caller. The skill's fallback (no subagents) was not exercised.

**Still needed before `stable`: a Codex pass.** At minimum the `db-decision` case (to see which
reviewer route Codex takes), one "should" trigger and one near-miss. Then change
`metadata.codex-check` in `SKILL.md` to `pass` and `status` to `stable`.
