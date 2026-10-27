# Trials: scrollback

House rule 8: tried in Claude Code (Haiku, Sonnet, Opus) and in Codex before `stable`.

| Agent | Eval cases | Triggers | State |
| :--- | :--- | :--- | :--- |
| Claude Code | 12 of 12 (4 cases x Haiku, Sonnet, Opus) after one fix. Pages pass `check_scrollback.py --shots` at 1280 and 375px, keep every figure and behaviour on a restyle, and split many series into small charts | 8 of 8 should, 8 of 8 near-miss (Haiku, Sonnet); near-misses went to `design`, `dataviz` and `diagrams` | done |
| Codex | not run | not run | **pending** |

Fix from the trials: Haiku added a chart to an existing Scrollback page with the general chart skill
(three colours and a legend) because the request didn't name Scrollback. Every page the starter makes
now opens with a comment naming the system and this skill, and the description names charts; on
rerun Haiku read the marker and switched to this skill.

After an independent review (no change to the jobs): printing keeps the frame rules, bars and panels
(`print-color-adjust: exact`); log timestamps, tree lines and placeholders moved off `--rule`, which
was under its own contrast floor; the checker's accent rule can no longer be passed by a second
selector, a look-alike class name or a custom-property alias, and it now reads `@container` blocks,
local `@import`s, every CSS colour name, emoji in generated content and attributes, SVG blur and
gradient elements, and paper tokens.

Script checks: `python3 evals/scrollback/regress.py` (static cases), or
`uv run --with playwright python evals/scrollback/regress.py --shots` to add the render and print
cases. After a stylesheet change, run `python3 evals/scrollback/regen_fixtures.py` first.

**Still needed before `stable`: a Codex pass.** At minimum `status-build`, `check-dashboard`, one
"should" trigger and one near-miss (4 runs). Then change `metadata.codex-check` in `SKILL.md` to
`pass` and `status` to `stable`.
