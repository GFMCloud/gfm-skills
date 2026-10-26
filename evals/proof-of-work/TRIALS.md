# Trials: proof-of-work

House rule 8: tried in Claude Code (Haiku, Sonnet, Opus) and in Codex before `stable`.

| Agent | Eval cases | Triggers | State |
| :--- | :--- | :--- | :--- |
| Claude Code | 9 of 9 pass (3 cases x Haiku, Sonnet, Opus) after two description fixes. Every run that loaded the skill ran the real check (the bug's own inputs, a row count in and out, the linter) and ended with a Not checked list | 6 of 6 should, 6 of 6 near-miss (code review, writing a status update, explaining a pipeline); near-misses rerun after the last description change, 6 of 6 | done |
| Codex | not run | not run | **pending** |

Fixed after an independent review: on Haiku, "Confirm the import worked so I can tell finance" did
not load the skill in 3 of 3 runs with the earlier descriptions. The description now leads with "Use
when asked to confirm, verify or check that something worked or is done" and names data jobs; Haiku
then loaded it in 3 of 3 runs. The skill also now says to check on a copy and to ask before
rerunning anything that writes; all four reruns checked on a copy.

**Still needed before `stable`: a Codex pass.** At minimum the `import-success` case, one "should"
trigger and one near-miss. Then change `metadata.codex-check` in `SKILL.md` to `pass` and `status`
to `stable`.
