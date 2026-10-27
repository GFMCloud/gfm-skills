# Phased project

Ordered steps of different kinds: look around, decide, do, check, then a finish that often can't
be undone (delete the old copy, publish, switch over).

## Files

```text
<project>/
├── AGENTS.md          what this is, rules, how to resume, never-do list
├── CLAUDE.md          one line: @AGENTS.md
├── STATE.md           resume point (template in SKILL.md)
├── END-STATE.md       the finished state, and the tie-breaker for unclear instructions
├── preflight.json     systems the work touches
└── phases/
    ├── 1-<name>.md    one file per phase
    └── ...
```

## END-STATE.md

Write the goal as a state that can be checked, not a task list: "every photo from `photos/` is on
the archive drive with the same size and checksum, and `photos/` is gone", not "move the photos".
Add the check that proves it (the command), and what is out of scope.

## A phase file

```markdown
# Phase 2: <name>
Kind: survey (read only) | decision | change | check | finish (can't be undone)
Needs: phase 1 done
Systems: <names from preflight.json>

## Steps
1. ...

## Done when
- <a check with a command, and what its output must show>
```

A phase with no checkable "Done when" isn't ready to run. Name the kind: the rules below hang on it.

## Gates

- **Decision gate**, after the survey: every decision that is the user's, in one batch, each with
  a recommendation and a one-line reason. Rows the user doesn't change are agreed as proposed.
  Later phases run only agreed rows; anything not agreed is skipped and reported.
- **Finish gate**, before anything that can't be undone: the exact list of what will be deleted,
  sent or replaced, where each item can still be recovered, and the evidence that the check phase
  passed. Wait for a yes to that list. It is never approved in advance, by a standing rule or by
  "just finish it".
- Add a gate only for a second decision of the same weight, and list the gates in `AGENTS.md` by
  name rather than saying "the two gates".
- When a ruling at a gate overrides a proposed step, say who now owns that step's side effects
  (clean-up, renaming), or they quietly vanish.

## Keep it undoable until the finish gate

- Nothing is deleted before the final check passes. Retire things by renaming or moving them to an
  archive folder, and say which convention the project uses.
- Move rather than copy when the goal is one home for something; two editable copies is often the
  problem being fixed.
- A rename is only undoable if the folder is in git or backed up. If a target has neither, the
  first phase sets that up before anything is renamed.

## The check and finish phases

- The check phase checks the end state from scratch: a fresh count or listing compared against the
  source, not a reread of earlier notes. A tick in `STATE.md` with no command and output is not a
  check.
- Prove a validator can fail before trusting it: give it one input that must fail and record that
  it did.
- The finish phase writes every leftover into `STATE.md` under Left over with an owner, a
  successor project, or "dropped" and why, before the project is called done.
