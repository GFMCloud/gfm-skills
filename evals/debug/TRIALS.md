# Trials: debug

House rule 8: tried in Claude Code (Haiku, Sonnet, Opus) and in Codex before `stable`. Since
decision 39 Sonnet stands in for Haiku in Claude Code trials.

| Agent | Eval cases | Triggers | State |
| :--- | :--- | :--- | :--- |
| Claude Code | Sonnet 4 of 4 (empty-export after a description fix; first run a MISS, see below), Opus 4 of 4; post-review reruns of empty-export and refund-500 on Sonnet pass | Sonnet: should 4 of 4, near-miss 4 of 4, near-misses rerun 4 of 4 on the final description. Baseline (Sonnet, no skill): right cause, no loop, no hypotheses, no seam test | done |
| Codex | not run | not run | **pending** |

Sonnet stands in for Haiku (decision 39); Haiku was not run.

## The one miss

On the first description, Sonnet did not load the skill for "out/orders.csv … has been coming out
empty since yesterday … Find out why and fix it" (it fixed the bug ad hoc, as the baseline did).
The description now carries those words ("X is broken or empty since Y, find out why and fix it");
the rerun loaded it.

Every workspace is built with `python3 evals/debug/make_workspace.py <case> <empty folder>` (DEMO
material only).

## Codex runs owed (not before 2026-11-02, and only with Graham's OK on the count)

Proposed: 6 runs.

1. `empty-export` (history, wrong-seam test trap)
2. `refund-500` (redaction, no network, replay loop)
3. `flaky-totals` (intermittent: rate first, then a pinned seed)
4. Should: "The import got really slow after my last commit. Figure out what's wrong." (slow-import)
5. Near-miss: "Did the import actually work? Check before I tell the team." (slow-import, one import run first)
6. Near-miss: "Plan how we'd fix the duplicate-rows bug before touching anything." (slow-import)

Then set `metadata.codex-check` to `pass` and `status` to `stable` if all six pass.
