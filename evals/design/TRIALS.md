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

**Still needed before `stable`: a Codex pass.** At minimum the `new-landing-branded` case, one
"should" trigger and one near-miss. Then change `metadata.codex-check` in `SKILL.md` to `pass` and
`status` to `stable`.
