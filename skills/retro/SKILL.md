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
- made a decision between real alternatives that should not be argued again;
- lost time the record shows, even with no commit: a run of calls that found nothing (one search
  rerun, one file or fact hunted for across many calls) or work stalled on something the agent
  couldn't see. One repeated read, or a long session that moved steadily, doesn't count.

Check from evidence, not from how it felt: `git log --since=<start>` and `git status` in the project,
and the session record (transcript, log or notes). If none apply, reply with one line and stop:
`No retro: no commit, failure, decision or lost time in this work.` Write no file. If the gate is
met but no lesson survives step 2, say that in one line instead of a list:
`Retro: <short title>   gate: <...>   nothing worth keeping`.

## 2. Ground every lesson in the record

You are not a reliable narrator of your own session; memory gives the tidy version. Each lesson
quotes or points to its evidence: a log line, a commit, an error message, a file and line. If the
record doesn't show it, it isn't a lesson. Don't fill a gap with what usually goes wrong.

## 3. Look at the setup, not only the mistakes

A lesson about what the agent got wrong often hides a fix to the setup around it. Before routing,
check the record for these four:

- **Navigation.** Time spent finding a file, command or fact. The fix is a one-line pointer where
  the next session starts reading, not a copy of what it points to.
- **Guardrails.** The record shows a mistake that a check could have caught. Before proposing a new
  check, open the files that would run one (package scripts, Makefile, hook folder, CI workflow).
  Often the check is already written and nothing calls it, or it fails without anyone noticing; then
  the lesson is to wire it in or repair it. Quote both the mistake and the file that shows the gap.
  If no hook or CI job runs any check at all, say so in the same lesson.
- **Tool economy.** Expensive or repeated calls: one file read five times, a full log dumped for one
  line, a slow command rerun to see the same result. The fix is a narrower command, a script or a
  pointer.
- **Information access.** Something the agent needed and couldn't see: server logs, a CI run, a
  read-only view of a service. The fix gives the next session a way to see it.

Each still needs its evidence from step 2. Judging the instruction files themselves (lines that
change nothing, files grown too long) is agent-setup's audit, not a retro lesson.

## 4. Route each lesson

| Lesson | Goes to |
| :--- | :--- |
| How the user wants the agent to work (a standing preference) | The agent's memory or the user's own instructions file |
| How this project builds, runs or deploys, or where to find things | The project's instructions file (for example `AGENTS.md` or `CLAUDE.md`) |
| A choice that is hard to reverse, surprising without its context, and a real trade-off (all three) | A decision record in the repo, where the project keeps them. Missing any of the three, it is not one |
| Something a script could catch every time | A check: a test, a hook or CI, or wiring in the check that already exists. Not a sentence |
| Something the agent couldn't see, or a slow way of looking | A setup change: a log written to a file, read-only access, a script. Show the exact command or config |
| The agent did the wrong thing and no script can catch it | An eval or regression case for the skill or prompt involved |
| True once, unlikely to recur | Nowhere. It stays in the retro |

A rule written into an instructions file states the rule, then the reason. The reason stops someone
deleting a rule they don't understand.

**Third time is a broken mechanism.** Before routing, look for earlier retros or rules about the same
kind of failure. If the failure already has two rules and happened again, don't add a third. Name
the rules that didn't fire and propose changing the mechanism (usually a script or hook instead of
prose).

Propose every edit, a hook, CI step or script included; make none. Instructions, memory, decision
records and checks belong to the user. Show the exact text or command and where it goes, and edit only
what they approve.

## 5. Output

```
Retro: <short title>   gate: <one or more of commit, failure, decision, lost time>
1. <lesson in one sentence>
   Evidence: <quote or pointer>
   Goes to: <destination and path>   Proposed: "<the rule, then the reason; or the exact command or config>"
2. ...
One-offs left here: <list or none>
```

If the project already keeps retros (a `retros/` folder or similar), save this there as
`YYYY-MM-DD-<slug>.md`. Otherwise reply only; don't create a new place for notes nobody will read.
