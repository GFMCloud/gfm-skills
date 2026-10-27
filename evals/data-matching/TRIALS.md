# Trials: data-matching

House rule 8: tried in Claude Code (Haiku, Sonnet, Opus) and in Codex before `stable`. All
fixtures are invented demo data (see each folder's `DEMO-DATA.md`).

| Agent | Eval cases | Triggers | State |
| :--- | :--- | :--- | :--- |
| Claude Code | Haiku 5 of 5, Sonnet 5 of 5, Opus 5 of 5; link-no-limits rerun on Haiku and Sonnet after fixes, both pass | Haiku and Sonnet: 4 of 4 should, 4 of 4 near-miss (join on a clean key, chart, add a column, confirm an import) | done |
| Codex | not run | not run | **pending** |

## Codex runs owed

No Codex runs before 2026-11-02, and then only with an agreed run count. Proposed minimum: 5 eval
cases plus 2 should and 2 near-miss triggers, on one model, 9 runs. The cases most worth seeing in
Codex: `link-no-limits` (does it ask before applying fuzzy matches?) and `rerun-with-known` (reads
XLSX with the standard library and proves the rerun).

## Fixed during the Claude Code trials

- A Haiku run wrote a rerun script that called the skill by its path on the author's machine. The
  skill now says to call a copy of `match.py` in the project, or rely on `run.json` and `--verify`.
- `groups.csv` now names each link's partner, rule and fuzzy score; a shared contact detail whose
  `--must-agree` value differs goes to review as "kept apart" instead of being skipped silently.
- Proposed limits varied widely when the user gave none; the skill now gives a starting point and a
  floor.

## Regression

`python3 evals/data-matching/regress.py` runs the script on the fixtures and checks the outcomes the
cases rely on (inputs unchanged, no fuzzy match without limits, chains held, identifiers that differ
never match, placeholders never match, known answers reused, `--verify` catches a changed input).

## Known limits

- Similarity is spelling-based: nicknames, other-language forms, abbreviations and renames come only
  from identifiers or known answers.
- Above a million pairs the script compares only names sharing a two-letter word start.
- Some runs printed whole input files before loading the skill; the skill's rules start once it is
  loaded.
