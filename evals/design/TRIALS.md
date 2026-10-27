# Trials: design

House rule 8: tried in Claude Code (Haiku, Sonnet, Opus) and in Codex before `stable`.

| Agent | Eval cases | Triggers | State |
| :--- | :--- | :--- | :--- |
| Claude Code | 9 of 9 pass (3 cases x Haiku, Sonnet, Opus) after fixes. Built pages start with the `Brand:` line, pass `check_page.py` with no sideways scroll at 390px, and invent no content; redesigns keep every field, name and handler | 6 of 6 should, 6 of 6 near-miss (deck to `decks`, pipeline to `diagrams`, design doc to none) | done |
| Codex | not run | not run | **pending** |

Fixes from the trials: the description now covers critiques (one Haiku run didn't load the skill);
a redesign with only the default brand keeps the page's own colours; screenshots go to
`.design-check/` beside the page; the tap-target warning measures a checkbox's label and ignores
off-screen skip links.

After an independent review (scripts and wording, no change to the jobs): `brand.py` accepts named
colours and rejects broken font values; `check_page.py` reads single-quoted and unquoted
attributes, fails a pasted brand block nothing uses, catches a focus style removed inside
`:focus-visible`, measures nav links in lists, and checks text contrast with `--shots`; a critique
writes its screenshots to a temporary folder, not the user's project; scripts are called from the
skill's folder with the project as the working directory. Rerun on the final skill: critique
(Haiku, Sonnet), redesign (Sonnet), new-landing-branded (Haiku), 4 of 4 pass.

**Still needed before `stable`: a Codex pass.** At minimum the `new-landing-branded` case, one
"should" trigger and one near-miss. Then change `metadata.codex-check` in `SKILL.md` to `pass` and
`status` to `stable`.

**2026-10-27, R12 real-task fixes (branch `fix/r12-trial-findings`):** SKILL.md text changed after
real-task trials on private projects (logs kept outside this repo). Earlier counts in this file
predate the change; rerun the triggers and cases before `stable`.
