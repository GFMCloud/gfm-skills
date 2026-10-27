# Trials: planning

House rule 8: tried in Claude Code (Haiku, Sonnet, Opus) and in Codex before `stable`.

| Agent | Eval cases | Triggers | State |
| :--- | :--- | :--- | :--- |
| Claude Code | Sonnet and Opus pass every case they ran on the final skill. Haiku passes risky-retention, fix-with-repro and new-build-class; on trivial-footer it loads the skill, changes nothing and stops, but writes a fuller plan than "two lines" (three tries at the wording); on plan-then-do and approved-plan-breaks it often does the right thing without loading the skill | Sonnet 4 of 4 should, 5 of 5 near-miss; Haiku 2 of 4 should ("think it through first" and the explicit delete request missed), 5 of 5 near-miss. Near-misses, should 4 and Haiku's should 2 ran on the final description; the other should runs on the one before, which had the same trigger phrases | **draft** |
| Codex | not run | not run | **pending** |

Known limit: the description lists risky kinds of change (deleting data, access, DNS, mail, money, a
schema), so it loads when the request names one. A request that hides the risk ("set KEEP_COUNT to
7") does not load it on Haiku or Sonnet; both models still warned about the deletions it would cause.

**Still needed before `stable`: a Codex pass** (at minimum `risky-retention`, `new-build-class`,
`plan-then-do`, one "should" trigger and one near-miss), and a decision on Haiku's trivial-plan
length. Then set `metadata.codex-check` to `pass` and `status` to `stable`.
