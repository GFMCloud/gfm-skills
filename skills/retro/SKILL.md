---
name: retro
description: Runs a short, evidence-based retrospective on a session or piece of work and sends each lesson to where it will be used next time (instructions, memory, a check, a decision record, or nowhere). Use after a fix, a failure or a decision. Not for status reports or meeting notes.
metadata:
  status: draft
  codex-check: "pending: not yet tried in Codex; must pass before stable"
---

# Retro

Most sessions teach nothing worth keeping, and a retro that says so in one line is correct. The goal
is the few lessons that change what happens next time, each landed where the next session will read
it.

## 1. Gate first

A retro is earned only if the work did at least one of these:

- produced a commit or a shipped change;
- hit a real failure (an error, a wrong turn, a rollback) and fixed or diagnosed it;
- made a decision between real alternatives that should not be argued again.

Check from evidence, not from how it felt: `git log --since=<start>` and `git status` in the project,
and the session record (transcript, log or notes). If none apply, reply with one line and stop:
`No retro: no commit, failure or decision in this work.` Write no file.

## 2. Ground every lesson in the record

You are not a reliable narrator of your own session; memory gives the tidy version. Each lesson
quotes or points to its evidence: a log line, a commit, an error message, a file and line. If the
record doesn't show it, it isn't a lesson. Don't fill a gap with what usually goes wrong.

## 3. Route each lesson

| Lesson | Goes to |
| :--- | :--- |
| How the user wants the agent to work (a standing preference) | The agent's memory or the user's own instructions file |
| How this project builds, runs or deploys | The project's instructions file (for example `AGENTS.md` or `CLAUDE.md`) |
| A structural choice that limits future work | A decision record in the repo, where the project keeps them |
| Something a script could catch every time | A check: a test, a hook or CI. Not a sentence |
| The agent did the wrong thing and no script can catch it | An eval or regression case for the skill or prompt involved |
| True once, unlikely to recur | Nowhere. It stays in the retro |

A rule written into an instructions file states the rule, then the reason. The reason stops someone
deleting a rule they don't understand.

**Third time is a broken mechanism.** Before routing, look for earlier retros or rules about the same
kind of failure. If the failure already has two rules and happened again, don't add a third. Name
the rules that didn't fire and propose changing the mechanism (usually a script or hook instead of
prose).

Propose the edits; don't make them. Instructions, memory and decision records belong to the user. Show
the exact text and where it goes, and edit only what they approve.

## 4. Output

```
Retro: <short title>   gate: <commit | failure | decision>
1. <lesson in one sentence>
   Evidence: <quote or pointer>
   Goes to: <destination and path>   Proposed text: "<the rule, then the reason>"
2. ...
One-offs left here: <list or none>
```

If the project already keeps retros (a `retros/` folder or similar), save this there as
`YYYY-MM-DD-<slug>.md`. Otherwise reply only; don't create a new place for notes nobody will read.
