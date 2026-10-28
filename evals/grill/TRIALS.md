# Trials: grill

House rule 8: tried in Claude Code (Haiku, Sonnet, Opus) and in Codex before `stable`.

| Agent | Eval cases | Triggers | State |
| :--- | :--- | :--- | :--- |
| Claude Code | Sonnet 5 of 5 and Opus 5 of 5 (after fixes from one independent review; `vague-and-delegate` needed one skill fix and one loosened expect line). Haiku: not run; Sonnet stood in for it in this wave | Sonnet: 4 of 4 should (two runs first broke the yes-wording rule; fixed and rerun), 5 of 5 near-miss | done for Sonnet and Opus |
| Codex | not run | not run | **pending** |

A baseline run without the skill (Sonnet, `host-move-round1`) read the files well and caught the
planted facts, but asked eleven questions at once, several with no recommendation or not worded so
"yes" accepts, mixed dependent questions into one round, and closed by offering a migration plan.

## Codex runs owed

Not before 2026-11-02, and only once the maintainer agrees a run count. Proposed: 9 runs.

- Eval cases `host-move-round1`, `signup-round2`, `vague-and-delegate` (3 runs): checks the round
  format, the push-back and the vague-answer rule without Claude Code's subagents.
- Triggers: `Grill me on the plan in DESIGN.md before I commit to it.` and `Stress-test my thinking
  on moving the app to a new host: ask me the questions.` (2 runs).
- Near-misses: `Plan this first: add CSV export to the weekly report.`, `Get independent opinions on
  whether to switch databases; I think I'm anchored.`, `Review DESIGN.md and tell me what's wrong
  with it.`, `Plan the migration that drops two columns from the scores table.` (4 runs).

## Known limits

- A single trial turn sees one round only; the multi-round loop is tested by handing the run a
  transcript (`GRILL-SO-FAR.md`) with the user's answers. A live multi-turn session is untested.
- The frontier is the model's judgment, not computed from a graph, so two questions in one round
  can still turn out to depend on each other. The user saying so reopens the branch.
