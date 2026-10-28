# Trials: intake

House rule 8: tried in Claude Code (Haiku, Sonnet, Opus) and in Codex before `stable`.

| Agent | Eval cases | Triggers | State |
| :--- | :--- | :--- | :--- |
| Claude Code | 9 of 9 pass (3 cases x Haiku, Sonnet, Opus). Every run left `install.sh` alone and quoted the agent-addressed README text as a flag without acting on it | 6 of 6 should, 6 of 6 near-miss | done |
| Codex | not run | not run | **pending** |

**Still needed before `stable`: a Codex pass.** At minimum the `skill-pack` case (the injection
text is the main risk), one "should" trigger and one near-miss. Then change `metadata.codex-check`
in `SKILL.md` to `pass` and `status` to `stable`.

**Open item, deferred:** for a skill pack, give each skill a fit row against the installed skills
(fold into an existing skill, improve one, new, or not needed). Build it with the first real pack
that needs it, so there is something real to test on.
