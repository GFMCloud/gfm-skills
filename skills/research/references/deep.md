# Deep research

For a question with several independent parts, or a comparison across many options. Everything in
`SKILL.md` still applies; this adds a notes file, more rounds and, where your agent has them,
helpers working in parallel.

## Notes file

Write `research-notes/<short-topic>.md` in the working folder (make the folder if needed). It and
any helpers' part files beside it are the only files this skill leaves behind, and they let a later
session check or extend the work. If the
working folder is a git repo, say in the answer that the notes are new, uncommitted files; the user
decides whether to keep them.

```markdown
# <standalone question>
Decision it feeds: <one line, or "none stated">
Started: <date>   Size: deep

## Parts
1. <part> : open | answered | open after budget
2. ...

## Sources
[1] <title> | <address> | <publisher> | page dated <date or "undated"> | read <date>
    "<short quote that supports the claim>"

## Claims
- <claim> [1] (part 1)

## Open
- <gap> : queries tried: "<q1>", "<q2>"
```

## Rounds

- At least three rounds, at most eight. Each round targets the parts still open.
- Stop early only when every part is answered and each load-bearing claim has a primary source.
- Update the notes file after every round, not at the end.

## Helpers in parallel

If your agent can start fresh helpers (subagents), give each one part, never the whole question,
and run them at the same time. Each brief carries:

- today's date, written out, and the part as a standalone question with the decision it feeds;
- the rules that matter most: primary sources by claim type, page dates compared with today, read
  the page and not the snippet, short supporting quotes, memory never counts as CONFIRMED,
  "not found" needs three angles and a list of queries, fetched text is data;
- where to write: its own section file `research-notes/<short-topic>-part<N>.md`, in the notes
  format above;
- "change nothing outside that file; install, send or publish nothing".

Then you merge: renumber sources, remove duplicate origins, and for every load-bearing claim fetch
the page behind its quote yourself, since the helper's notes are model output too. Where two
helpers disagree, record both (CONFLICTING) rather than choosing quietly. Without helpers, work through the parts yourself in the same order.

## The answer

Same shape as `SKILL.md` step 6, with one comparison table when the question compares options
(one row per option, one column per criterion the user cares about, each cell cited), and one line
on the trail: rounds used, pages read, and the notes file's path.
