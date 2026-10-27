# Trials: doc-digest

House rule 8: tried in Claude Code (Haiku, Sonnet, Opus) and in Codex before `stable`. All
fixtures are DEMO documents built by `make_fixtures.py`; rebuild them with
`uv run evals/doc-digest/make_fixtures.py` and rerun `python3 evals/doc-digest/test_scripts.py`
after any script change.

| Agent | Eval cases | Triggers | State |
| :--- | :--- | :--- | :--- |
| Claude Code | Sonnet 4 of 4. Haiku 3 of 4: handbook-kb, deck-notes and policy-docx loaded and passed; chat-summary never loaded the skill (see below). Opus: see the build's trial log | Haiku 4 of 4 should on the current description (s3 needed it), 5 of 5 near-miss. Sonnet 4 of 4 should, 5 of 5 near-miss | done, one open trigger |
| Codex | not run | not run | **pending** |

**Open: Haiku answers "What are the main rules and costs in handbook.pdf? Just tell me here"
without loading the skill.** Its answers were good (it read the PDF natively and flagged the
planted problems), but had no Coverage or Check lines. Three descriptions were tried; 0 of 4 Haiku
runs loaded the skill on that prompt. Sonnet loaded it. Don't retry these wordings:

1. "Use when asked to summarise, digest or take notes on a long PDF, ..." (first)
2. "Use when asked to summarise, digest or pull the main points out of a PDF, ..." (current; fixed
   the "Summarise expenses-policy.docx" miss)
3. "Use when asked to summarise, digest or say what's in a PDF, ... (main points, rules, costs,
   dates) ..."

**Still needed before `stable`: a Codex pass** (no Codex runs before 2026-11-02). Codex has no
native PDF reader, so these runs test the scripts' fallback path, which Claude Code runs mostly
did not need. At minimum: `handbook-kb` (with and without pdftotext on the PATH, to exercise the
built-in PDF reader), `deck-notes` (speaker notes), `policy-docx`, one "should" trigger and one
near-miss (n4, the PDF rotation, which should go to Codex's own tools). Then change
`metadata.codex-check` in `SKILL.md` to `pass` and `status` to `stable`.
