# Trials: teach

House rule 8: tried in Claude Code (Haiku, Sonnet, Opus) and in Codex before `stable`.

| Agent | Eval cases | Triggers | State |
| :--- | :--- | :--- | :--- |
| Claude Code | Sonnet 4 of 4 and Opus 4 of 4; `sql-start` on Sonnet first missed NOTES.md (skill text fixed, then rerun clean). After one independent review, `sql-start`, `dns-next` and `mission-shift` rerun on Sonnet, all pass. Haiku: not run; Sonnet stood in for it in this wave | Sonnet: 4 of 4 should, 5 of 5 near-miss (doc-digest, research, diagrams, none, long-project) | done for Sonnet and Opus |
| Codex | not run | not run | **pending** |

A baseline without the skill (Sonnet) wrote a five-part course into chat at once for the P&L
request (no folder, no mission questions), and on the DNS resume followed the existing folder well
but did not mark the contradicted record, tried to open the lesson in a browser pane, and wrote a
lesson with no recall question in its practice.

## Codex runs owed

Not before 2026-11-02, and only once the maintainer agrees a run count. Proposed: 8 runs.

- Eval cases `sql-start`, `dns-next`, `pl-no-folder` (3 runs): the cold start (ask where and why),
  setting up the folder and the first lesson, and picking up from records, all without Claude
  Code's research skill being loaded the same way.
- Triggers: `Teach me how DNS actually works, over a few sessions.` and `Next DNS lesson please, I
  did the last quiz.` (2 runs).
- Near-misses: `Summarise dns-guide.pdf for me.`, `Explain what a CNAME record is in two
  sentences.`, `We're moving all 40 pages in wiki-migration/ to the new wiki over the next few
  weeks. Set it up so any session can carry on.` (3 runs).

## Known limits

- A trial turn sees one session. The loop across sessions (lesson, the learner reports back,
  record, next lesson) is tested by fixtures that stand for earlier sessions, not by a live
  learner over a week.
- `scripts/check_lesson.py` checks a lesson's shape (sections, one primary source, recall-first
  practice, self-contained), not whether it teaches well or is correct. Content accuracy rests on
  the sources and on the research skill.
- No trial run opened its lesson in a browser (the skill tells it not to open the file). The build
  session clicked every trial lesson headless at desktop and phone width: all-right and all-wrong
  scores came out right, no page errors; one wide table scrolled the page sideways at phone width,
  and the template now keeps tables scrolling in place.
- Runs without PostgreSQL or pandas checked examples in SQLite or by hand, and said so. A lesson's
  worked example can still be wrong for the learner's real version.
- Whether the mission-change record and `## Changes` line get written on the learner's yes is not
  tested: no case gives the yes.
