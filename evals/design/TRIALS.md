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

## Taste-craft fold (2026-10-28, branch `fold/design-taste-craft`)

For pages that present a business, person, product or event: a subject inventory, the idea
sentence with a competitor test, claims and a copy deck before markup, a look-and-fix loop on the
screenshots (at most three rounds), pictures from open collections (search, then ask before
downloading; build with the fallback meanwhile; credit on the page), `data-sample` for sample list
items, and a marketing-copy exception in Redesign. `check_page.py --shots` gains the frame checks
(outer margins, huddled sections, blank stretches, the h1 on the first screen, a heading on every
section, titles at most two lines) after one scroll through the page; `--screen` turns them into
warnings for everything else. Method from Leonxlnx/taste-skill (MIT), written fresh; only dated,
linked study numbers are quoted. All trials on Opus (visual build).

| Agent | Eval cases | Triggers | State |
| :--- | :--- | :--- | :--- |
| Claude Code (Opus) | 6 of 6 pass: `stock-landing-taste`, `juror-critique-frame` and `restaurant-onepage`, plus the host cases `new-landing-branded`, `redesign-signup` (treated as a form, ran with `--screen`, every field, id, action and handler kept) and `critique-pricing`. The first restaurant run searched no open collections; after the picture step was reworded, the rerun searched Wikimedia Commons, named four pictures with licences and downloaded none. `stock-landing-taste` and `juror-critique-frame` passed again on the final text | 4 of 4 should, 4 of 4 near-miss (deck to decks, pipeline to diagrams, design doc to second-opinion, launch check to deploy-verify). The description is unchanged, so these ran on the installed copy | **draft** |
| Codex | not run | not run | **pending** |

Baseline (the card's Opus probe, same prompts, design before this fold): the "properly designed"
run kept the stock copy and moved to a paper ground with mono numbering; the restaurant page was a
text column in the left half of the screen with the menu left as NEEDS YOUR INPUT. With the fold:
the stock page was rebuilt around a sample invoice drawn from the product's own facts, with every
stock line rewritten and listed and the unsourced quote flagged; the restaurant page filled the
width, used the ironmonger's sign as its masthead and showed the full menu with four `data-sample`
dishes.

Fable review: ten rounds. Rounds 1 to 9 found checker false positives and false negatives on
ordinary layouts (margins, card grids, app roots, scroll boxes, scroll reveals, smooth scrolling,
heroes inside headers) and some contradictions in the text, all fixed and rechecked on about 170
test pages kept outside the repo. Round 10 found nothing serious.

Known limits: the frame checks are heuristics. A colour field, gradient or CSS shape counts as
empty, so a picture needs `img`, `svg`, `canvas`, `role="img"` or a background image; FAQ
questions set as a section's first `h2` count as titles.

Codex runs owed for this fold (only with the maintainer's OK on the count): 3, namely
`restaurant-onepage`, `juror-critique-frame` and `redesign-signup`.
