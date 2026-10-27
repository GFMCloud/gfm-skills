# Trials: research

House rule 8: tried in Claude Code (Haiku, Sonnet, Opus) and in Codex before `stable`.

| Agent | Eval cases | Triggers | State |
| :--- | :--- | :--- | :--- |
| Claude Code | Opus 4 of 4 loaded and passed (plus the `sed-claim` rerun after the scratch-folder fix). Haiku and Sonnet: every run that loaded the skill met its expect lines; loading is the gap (see below) | 8 of 8 should, 8 of 8 near-miss (4 each, Haiku and Sonnet). Two Haiku runs (s1, n1) wrote no RESULT.md, citing a rule against report files; graded from their replies and TRACE lines | done, one open border |
| Codex | not run | not run | **pending** |

**Open border with doc-vs-reality.** When the claim to check sits in a named file ("check whether
BRIEF.md's findings still hold", "is item 3 in PLAN.md still right?"), Haiku and Sonnet often load
doc-vs-reality or nothing. Those runs still gave right answers, without this skill's claim table,
dated sources and memory labels. Descriptions tried, with research loads on the file-based cases
(stale-brief, open-issue, sed-claim) on Haiku and Sonnet:

1. "Researches questions about the world as it is now and checks whether claims, versions or
   statuses are still true, citing dated primary sources. Use when asked to research, look up,
   compare options or fact-check something. ..." : 0 of 6.
2. (current) "Use when asked to research or look something up, or whether a claim, plan or research
   finding is still true today. ..." : 2 of 6.
3. "Use when asked to research or look something up, or whether a claim in a brief, plan or wiki
   about the outside world (a release, support date, feature, behaviour, price) still holds. ..." :
   0 of 4.

Don't retry these. The likely fix is an exclusion in doc-vs-reality's own description. The `sed-claim` case is met by most runs with or without the skill, so it mostly tests the
model; keep it for the scratch-folder rule.

**Still needed before `stable`: a Codex pass** (no Codex runs before 2026-11-02). At minimum the
`open-issue` case (the injection line and the stale-open ticket), the `stale-brief` case (needs
Codex web search enabled; without it, the run must say it could not check rather than answer from
memory), the `no-web` case, one "should" trigger and one near-miss. Then change
`metadata.codex-check` in `SKILL.md` to `pass` and `status` to `stable`.

**2026-10-27, R12 real-task fixes (branch `fix/r12-trial-findings`):** SKILL.md text changed after
real-task trials on private projects (logs kept outside this repo). Earlier counts in this file
predate the change; rerun the triggers and cases before `stable`.
