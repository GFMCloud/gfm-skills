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

## Spec-slices fold (2026-10-28)

Decided assumptions, vertical slices with `blocked by`, the test seam in Done when, and a diff check
in step 6, plus a new description naming specs and slices and the grill and wizard borders. Haiku
was not run (Sonnet stands in, decision 39).

| Agent | Eval cases | Triggers | State |
| :--- | :--- | :--- | :--- |
| Claude Code | `decided-slices` Sonnet and Opus pass; `diff-vs-plan` Opus passes, Sonnet does the right thing without loading the skill (0 of 2 loads); host `fix-with-repro` and `risky-retention` pass on Sonnet | Sonnet: should 7 of 8 on the final description (should 2 loads 2 of 3 across waves), near-misses 6 of 6; grill's 4 and wizard's 5 should-prompts still go to their own skills, and their planning near-misses come here | **draft** |
| Codex | not run | not run | **pending** |

Known limits: Sonnet does not load planning for "finish off an approved plan" (it does the diff
check anyway). "Specs or slices" in the description is a summary of the trigger, not the user's
quoted words; on Sonnet the spec, blocks and slices prompts and the explicit delete request went
from 0 of 4 (old description) to 4 of 4.

Codex runs owed for this fold (not before 2026-11-02, and only with the maintainer's OK on the count): 5,
namely `decided-slices`, `diff-vs-plan` (after `prepare.sh`), should 5 (spec), should 7 (slices) and
near-miss 4 (note of what we decided).
