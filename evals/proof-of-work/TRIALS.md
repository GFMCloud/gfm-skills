# Trials: proof-of-work

House rule 8: tried in Claude Code (Haiku, Sonnet, Opus) and in Codex before `stable`.

| Agent | Eval cases | Triggers | State |
| :--- | :--- | :--- | :--- |
| Claude Code | 8 of 9 pass (3 cases x Haiku, Sonnet, Opus) after a description fix. Every run that loaded the skill ran the real check (the bug's own inputs, a row count in and out, the linter) and ended with a Not checked list | 6 of 6 should, 6 of 6 near-miss (code review, writing a status update, explaining a pipeline) | done, one open item |
| Codex | not run | not run | **pending** |

**Open:** on Haiku, "Confirm the import worked so I can tell finance" did not load the skill in 3
of 3 runs, across three descriptions. The answer was right each time but without the report format.
Waiting on the maintainer's call; not accepted as a known gap.

**Still needed before `stable`: a Codex pass.** At minimum the `import-success` case, one "should"
trigger and one near-miss. Then change `metadata.codex-check` in `SKILL.md` to `pass` and `status`
to `stable`.
