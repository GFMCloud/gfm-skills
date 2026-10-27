# Split: a strong model plans, a cheaper one executes

Judgment is expensive and labour is cheap. In a split, a session on the strong tier reviews the
project and writes a plan; a fresh session on a cheaper tier carries it out; a strong session checks
the result. **The plan file is the only thing the executor sees**, so everything here serves one
rule: the plan must stand on its own.

Steps: model check, read, review, write the plan, stop for a yes, kickoff, verify.

## 1. Model check

Look at which model this session runs on (your context usually says). If it is not on the strong
tier for this agent (`models.md`), say so and let the user choose: restart on the strong tier, or go
on knowing the review depth is the point of a split. Don't carry on silently.

## 2. Read before judging

- The folder tree (skip dependencies, build output, `.git` internals), the README and other docs,
  the last 20 commits (`git log --oneline -20`), entry points, config, then the core source.
- Any earlier `improvement-plan-*.md` or `verification-*.md` in the project.
- The project's goal. If nothing in the project states one, ask the user for one sentence before
  reviewing: without a goal, a review is taste.

## 3. Review

Cover structure, correctness risks, docs against reality, the user-facing surface (UI, CLI output,
generated files), consistency, and gaps between the goal and what exists. For each finding:

- Severity: **Critical** (broken or misleading), **High** (will bite soon), **Medium** (friction),
  **Low** (polish). At most five Low findings; count the rest.
- The file and line, or the section. A finding without a location can't be executed.
- Skip what a formatter, linter or CI check already enforces, and anything in generated files.
- A clean area gets one line saying so. Don't invent findings to look thorough.

## 4. Write the plan

Save it in the project root as `improvement-plan-<YYYY-MM-DD>.md`. If that name exists, add `-v2`
(and so on). Never overwrite an earlier plan or verification report.

```
# Improvement plan: <project>
Reviewed: <date> on <model>   Executor: <recommended model and effort>   Version: <v1 | v2, supersedes ...>

## Goal            one paragraph; every item traces back to it
## What was read   the files, docs and commit range actually read
## Summary         counts by severity and the three items that matter most
## Order           item IDs in execution order, with dependencies
## Items           one block per item, below
## Not in scope    what the executor must leave alone across the whole plan
## For the executor  how to run checks, where tests live, what to do when stuck
## Tracking        a table of item ID and status, for verify
```

Each item:

```
### WI-<nn> <title>  (<severity>)
Files: <exact paths>
Now: <a few lines quoted exactly from the current file>
Change to: <the concrete end state>
Done when: <checks that need no judgment: a command that exits 0, a string that is gone, a test that passes>
Leave alone: <nearby things not to touch>
```

Before finishing, reread every item and ask: could a model that never saw this session do it
correctly? Remove anything that only makes sense here ("as discussed", "the issue above"). Item IDs
never change once assigned; verify and follow-up plans refer to them.

## 5. Stop for a yes

Show the plan and stop. The plan is the cheapest place to cut or reorder; execution can take hours.
Write the kickoff only after the user agrees.

## 6. Kickoff

Recommend an executor tier with a reason: the default tier for well-specified, mechanical items;
the strong tier when items still need judgment or touch many files. Then give one command for a
fresh session (exact model names and flags from `models.md`):

- Claude Code: `claude --model <model> "<kickoff>"`
- Codex: `codex -m <model> -c model_reasoning_effort="<level>" "<kickoff>"`
- A chat app: a block to paste into a new conversation, plus which files to attach (the plan, and
  the project files if the new session can't reach them).

The kickoff text: read `<plan file>` and carry out its items in the order given; check each item's
"Done when" before marking it done; stay inside the plan; update the Tracking table. It never refers
to this session. Anything the executor needs goes in the plan.

## 7. Verify

Checking the executed plan is a "did it work?" job: use the `proof-of-work` skill if it is
installed. Either way, go item by item through the plan: **Done**, **Partial** or **Missed**, each
with evidence from running the item's "Done when" check (the file and what changed or didn't),
never from the Tracking table. Then look for regressions outside the plan's scope. Save
`verification-<YYYY-MM-DD>.md` beside the plan. If anything is Partial or Missed, write a follow-up
plan with only those items, in a new file, in the step 4 format, keeping their IDs.
