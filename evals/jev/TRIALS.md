# Trials: jev

House rule 8: tried in Claude Code (Haiku, Sonnet, Opus) and in Codex before `stable`. All fixtures
are invented demo projects (see each folder's `DEMO-DATA.md`). The trial machine had no
`TYPESAFE_API_KEY` set and no SDK installed, so no trial made a real Jev call.

| Agent | Eval cases | Triggers | State |
| :--- | :--- | :--- | :--- |
| Claude Code | Haiku 4 of 4 (fit-scan and replace-llm-call passed on rerun, after a fixture fix and a fit-gate wording fix), Sonnet 4 of 4, Opus 4 of 4 | Haiku and Sonnet: 4 of 4 should, 4 of 4 near-miss (list matching, model choice, plain release notes, plain keyword fix) | done |
| Codex | not run | not run | **pending** |

## Codex runs owed

No Codex runs before 2026-11-02, and then only with an agreed run count. Proposed minimum: 4 eval
cases plus 2 should and 2 near-miss triggers, on one model, 8 runs. The cases most worth seeing in
Codex: `private-data-rule` (does it refuse to let the project's rule widen the user's?) and
`build-issue-triage` (copies and fills the templates, runs the offline gate test).

## Fixed during the Claude Code trials and review

- The `fit-scan` fixture's review file now comes from the matcher's real output; the first version's
  scores didn't match the code.
- The fit gate says Jev judges the same packet today's step already gets, asks for a cost estimate
  both ways and a baseline from the current rule, and states the floor of about 20 known answers.
- `evaluate.py` refuses a real run without the key, writes nothing when no item was judged (so the
  held-out set isn't used up by a failed start), and parses `--trials` strictly.
- `preflight.py` never follows a symlinked project rule, cuts long rule lines, skips code fences and
  shows home paths as `~`.
- The gate rejects out-of-range or boolean Score values, non-dict answers and non-string choices;
  the offline test attacks each.

## Checks a person runs

- One real call on one public item with a key (the maintainer or another user): run `python3
  test_questions.py`, then `python3 evaluate.py tuning` on a small labelled set, and confirm the
  `ask()` reading of the real response, the model check and the printed spend.

## Known limits

- The SDK boundary (`to_sdk()`, `ask()`) was checked against the provider's docs on 2026-10-27, not
  against a live response.
- Results on a few dozen known answers are rough; the skill says so, but the fixtures can't show how
  rough.
