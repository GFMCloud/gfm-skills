# Map

## Contents
Files, MAP.md, A question file, Question types, Charting (the set-up session), Working a question
(every later session), Running questions in parallel, Finished.

The end is known but the route is not: too many open decisions to plan yet ("map out what we need
to decide before we build"). The project's output is decisions, not the build. Each session settles
one open question; the map is done when nothing is left to decide, and the build then goes to the
planning skill (one sitting) or a phased project (many sessions).

If every decision is already clear and the work fits one session, there is no fog: say so and
plan it instead of setting up a map. If the user wants the decisions settled in one sitting
("today", "this afternoon"), it is not a map either: settle them in the conversation (the grill
skill, if installed) or plan the change (the planning skill), and write no project folder.

## Files

```text
<project>/
├── AGENTS.md          what this is, rules, how to resume, never-do list
├── CLAUDE.md          one line: @AGENTS.md
├── STATE.md           resume point (template in SKILL.md); Progress and Decisions say "see MAP.md"
├── preflight.json     systems the questions read (the code or data being decided about)
├── MAP.md             destination, index of decisions, fog, out of scope
└── questions/         one file per sharp question: <name>.md
```

`MAP.md` is the only decision list: `STATE.md` points to it rather than keeping its own.

**Preflight.** List the systems the questions read: the code, data or accounts being decided
about. Public sources a research question reads (web pages, docs) are not systems; cite them in
its Answer. If no question reads anything outside the project folder yet (a course outline, a
pricing choice), leave out `preflight.json` and `tools/`, and make the second line of `AGENTS.md`:
"No preflight yet: before the first question that reads a system, add one (long-project steps
3.2 and 4)."

## MAP.md

```markdown
# Map: <project>
## Destination
<one or two lines: the decision, spec or change that closes this map>
## Notes
<standing preferences, skills every session should use, who decides what>
## Decisions so far
<one line per answered question: its name, a one-line gist, the file. Never the detail>
## Not yet specified
<the fog: decisions you expect but can't yet word precisely, and what each waits on>
## Out of scope
<what this effort deliberately won't decide, one line why. These never come back as questions>
```

Open questions are not listed in `MAP.md`; their files are the list (`grep -l '^Status: open'
questions/*.md`, and `'^Status: claimed'` for the ones in hand).

## A question file

```markdown
# <name: the question's gist, a few words>
Type: research | grill | task
Status: open | claimed <date> by <session or person> | answered <date> | out of scope <date>
Blocked by: <names of other questions, or none>

## Question
<one sharp question, small enough for one session>

## Answer
<written only when it is settled: the answer, its evidence, and what it unblocks>
```

**Refer to questions by name**, in `MAP.md`, `STATE.md` and every reply ("the region question"),
never by a bare number. The file name is the name in lowercase with hyphens. `Blocked by:` keeps
the names of blockers already answered; the Status of each tells you whether it still blocks.

**Sharp or fog?** A question gets a file when you can state it precisely now, even if it is blocked
and can't be answered yet. If you can't phrase it that sharply, it stays under Not yet specified as
a loose line. Don't cut the fog into question-sized pieces in advance.

## Question types

- **research** (agent alone): a fact outside this folder that a decision waits on. Use the research
  skill if it is available; the answer cites dated sources.
- **grill** (with the user): a choice only the user can make. Use the grill skill if it is
  installed; otherwise ask in plain conversation, each question with your recommended answer. Never
  answer the user's side yourself: until the user replies, the question stays claimed, not answered.
- **task**: hands-on work a decision depends on (get access, pull a sample, measure a size). Do it
  when `AGENTS.md` allows it; otherwise give the user an exact checklist. Its Answer lists the steps
  taken and the facts later questions need. A task never does the build itself.

A question is **done** when its Answer holds the answer and its evidence: the sources with dates,
the command with its output, or the user's own words with the date they said them.

## Charting (the set-up session)

1. Propose the destination from what the user said; it goes in SKILL.md step 3's one batch of
   questions, because it fixes the scope.
2. Go wide, not deep: list every open decision you can see. Sharp ones get a file; the rest go under
   Not yet specified; anything past the destination goes under Out of scope.
3. Wire `Blocked by:` lines after all the files exist, using the names.
4. Answer nothing, unless the user asked to start.

## Working a question (every later session)

1. Read `AGENTS.md`, `STATE.md` and `MAP.md`, and run the preflight if the folder has one. Open
   other question files only when you need them.
2. Pick one question: the one the user named, else an open one whose blockers are all answered,
   preferring the one that blocks the most others. Skip a claimed question: another session has it.
   A claim from an earlier day with no Answer may be stale: never clear it yourself; list it under
   Problems found and ask the user, who sets it back to open. It stays skipped this session.
3. **Claim it first**: set its Status to `claimed <date> by <session or person>` before any work.
4. Work it as its type says, and write the Answer with its evidence.
5. Then, in `MAP.md`: add one line under Decisions so far; move any fog the answer made sharp into
   new question files (and off the Not yet specified list); mark a question the answer made
   pointless `out of scope <date>` with one line under Out of scope; fix `Blocked by:` lines it
   changed. Update `STATE.md`'s next step.
6. **An answer that undoes another.** If it contradicts an earlier decision or changes another
   question's wording, don't edit that file. Say so under Problems found; on the user's yes, set the
   earlier question back to `open` with one line why (its old Answer stays below as history), and
   mark its Decisions so far line `reopened <date>`.
7. **One question per session.** Stop there, even if the next one looks easy.

## Running questions in parallel

Only research questions run in parallel. Each helper gets one question and writes only that file
(claim, then answer); it never edits `MAP.md`, `STATE.md` or another question's file. The main
session alone writes `MAP.md` and `STATE.md`, folding each answered file into the map afterwards.

## Finished

The map is done when no question is open or claimed and Not yet specified is empty. A fog line
that no answer sharpened is either worded now as a question or ruled out of scope with the user.
Check it from the files (fresh `grep`s for open and claimed), add a "Hand-off" line under Left over
naming where the build goes (planning or a phased project) and which decisions it rests on, and
stop: don't start the build in the map.
