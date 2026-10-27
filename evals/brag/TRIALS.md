# Trials: brag

House rule 8: tried in Claude Code (Haiku, Sonnet, Opus) and in Codex before `stable`.

| Agent | Eval cases | Triggers | State |
| :--- | :--- | :--- | :--- |
| Claude Code | Haiku 4 of 4, plus 4 of 4 reruns after the review fixes; Sonnet 4 of 4, plus 1 of 1 rerun; Opus 4 of 4 (on the fixed skill) | Haiku 3 of 3 should, 5 of 5 near-miss; Sonnet 3 of 3 should, 5 of 5 near-miss (near-misses rerun on the final description) | done |
| Codex | not run | not run | **pending** |

Trials could not install packages. On the test machine the system Python already had Playwright and
Chromium, so light-mode runs did render (15 videos across the waves, lengths confirmed with ffprobe); nothing was
downloaded. Full mode (Hyperframes) was never run, because it downloads a package. A render on a
clean machine, and any full-mode render, is a check for the maintainer (see "Render checks" below).

Regression script for the helper scripts: `python3 evals/brag/regress.py` (60 cases on made-up
inputs, one or more per review finding).

## Render checks (run by hand)

1. Light mode, in a copy of `files/pantry-pal` after a light-mode run:
   `uv run --with playwright python skills/brag/scripts/render_light.py <copy>/brag-output/composition`,
   then `python3 skills/brag/scripts/poster.py <copy>/brag-output <seconds>`.
2. Full mode, after a full-mode run: from `<copy>/brag-output/composition`,
   `npx hyperframes doctor && npx hyperframes lint . && npx hyperframes render -o ../brag.mp4`
   (downloads the Hyperframes package on first use).

**Still needed before `stable`: a Codex pass** (at minimum `plan-project`, `light-vertical`, one
"should" trigger and one near-miss). Then set `metadata.codex-check` to `pass` and `status` to
`stable`.
