---
name: long-project
description: Sets up, resumes and finishes work spanning many sessions (phased projects, sweeps over many items, experiments, registers of findings to recheck later) in files any session can pick up. Proves access to every system first. Use for multi-session work or to carry it on. Not for one-sitting tasks.
metadata:
  status: draft
  codex-check: "pending: not yet tried in Codex; must pass before stable"
---

# Long project

A project that outlives one session lives in files, not in the conversation. The test for every
file you write: could a fresh session, with no memory of this one, carry on from the files alone?

**Before any work starts, run the preflight (step 4): a real read and a real write to every
system the work needs. If one fails, stop, report every blocker at once, and don't work around it.**

## 1. Check it is a long project

Set one up only when both hold:

- **It won't fit in one session.** Days of work, more items than one context can track, or a
  project that keeps going (a model you keep tuning).
- **Each part has a checkable "done".** A phase, item or run can be shown finished with a command
  and its output.

Otherwise say which test fails and do the right thing instead: do the task now, or write a short
to-do list. A scheduled repeat ("every morning") is a scheduling job, not this. A brand-new repo
for the work is the project-start skill's job first; this project's folder then sits beside it.

## 2. Pick the shape

| Shape | Fits when | Core of it | Read |
| :--- | :--- | :--- | :--- |
| Phased | Ordered steps of different kinds, often ending in something you can't undo (delete, publish, cut over) | An end state written as a state, gates before decisions and before the last step | `references/phased.md` |
| Sweep | Many items, one treatment ("every doc", "all repos") | A frozen list of items, one state file per item, one item planted to fail | `references/sweep.md` |
| Experiment | No finish line: tuning, modelling, analysis | Predictions written before results, one file per run, a dead-ideas list | `references/experiment.md` |
| Rulings | Measured decisions that may go stale ("A is faster than B") | One file per decision with its evidence, what would prove it wrong, and a recheck | `references/rulings.md` |

Read only the reference for the shape you pick. Shapes combine: a phase can be a sweep, and any
project can keep a rulings folder.

## 3. Set it up

1. **Ask once.** Propose answers yourself from what the user said and the files you can see, then
   ask everything that is still open in one batch. Never invent a value: an unknown stays `TBD`,
   and the project's instructions say to stop on a `TBD` that the next step needs.
2. **Make a new folder named after the project** (unless the user names one), beside the thing
   being changed, not inside it, so the record survives the work. Every shape has:
   - `AGENTS.md`, whose first line is: "Start of every session: if a skill named `long-project` is
     available, load it before reading on." Then what this is, the rules below that apply, what may
     go ahead without asking, what never to do, and how to resume. Add a one-line `CLAUDE.md`
     containing `@AGENTS.md` so Claude Code reads the same file.
   - `STATE.md`: the one place a session resumes from (template below).
   - `preflight.json` and `tools/preflight.py`, a copy of this skill's `scripts/preflight.py`, so the
     project runs the same check in any agent and on any machine. Never write the skill's own path
     into the project.
   - the shape's own files, from its reference.
3. **Write it fully.** No leftover `<placeholder>`; check with
   `grep -rn --exclude-dir=tools '<[a-zA-Z][^>]*>' <folder>` (a sweep's `state/<id>.md` is the
   one expected hit).
   Lists and counts live in one file (the manifest, the register, the phase list); other files
   point to it rather than repeat a number that will go stale.
4. **Set up only.** Don't start the work in the setup session unless the user asked for that too.
   Write a helper script only when the done-check needs one, and keep it under about 60 lines.

`STATE.md` template:

```markdown
# State
Status: not started | in progress: <phase or batch> | done (<date>)
Next step: <one line a fresh session can act on>

## Progress
<phases with checkboxes, or "see MANIFEST.tsv and state/", or "see REGISTER.md">

## Evidence
<commands and their real output: the preflight report, each check that a step is done>

## Decisions
<date, decision, who made it, one line why. Append only>

## Problems found
<date, what, where, suggested fix. Raised at the next gate, not one by one>

## Left over
<what is still open, why, and who owns it next>
```

## 4. Preflight: prove access before work starts

List every system the work reads or changes: folders and drives, git repos and their remotes,
APIs and accounts, command-line tools, other machines. Every target named in the end state, the
worker steps or the holdout is a system; one whose location you don't know yet is a blocker, not
something to leave out. Write `preflight.json` in the project folder and run
`python3 tools/preflight.py preflight.json` from there (`--check` validates without running
anything). Paths are relative to the project folder.

```json
{
  "project": "move photos to the archive drive",
  "systems": [
    {
      "name": "archive drive",
      "covers": "../archive-drive only, and that it is the drive, not a plain folder on this laptop",
      "fix": "plug in the archive drive so it mounts at archive-drive/; don't create that folder by hand",
      "read":    { "run": "cat ../archive-drive/DRIVE-ID.txt", "expect": "contains:shop archive" },
      "write":   { "run": "printf ok > ../archive-drive/.preflight && cat ../archive-drive/.preflight && rm ../archive-drive/.preflight", "expect": "contains:ok" },
      "control": { "run": "cat ../archive-drive/NO-SUCH-ID.txt", "why": "the same read without the marker file must fail" }
    }
  ]
}
```

- **Real targets.** Read the thing the work will read; write the smallest thing to where the work
  will write (never into a folder the work only reads), then remove it. A probe never creates its
  target (no `mkdir`; the script rejects it): a missing target is the failure you are looking for.
  `expect` is `nonempty`, `contains:TEXT` or `number>=N` (the first number in the output, so make
  the count the only output, as with `| wc -l`); a command that ran but found nothing doesn't
  count. For a folder that may be empty (a new destination), read `ls -ld <folder>` with
  `nonempty`: a count of its contents is 0 there and proves nothing, and a bare `test -d` prints
  nothing, so it never meets an evidence rule. A system the work only reads gets
  `"write": "not needed: <why>"`. Prove identity where a stand-in could pass: an empty folder passes
  `ls` as well as a mounted drive, so read a marker file on the drive (or compare device ids).
- **A control that must fail.** The read command pointed at a path that doesn't exist, or run
  without the credential or against a remote that doesn't exist. A control changes nothing: never
  delete, move or overwrite something to make it fail (the script rejects the common ones: rm, mv,
  cp, tee, touch, a redirect). If the control succeeds, the read proved nothing; if it fails only
  because the command is missing or doesn't parse, it proved nothing either, and the script says
  so. For a write that creates something on a server, the control is the same request with a
  required field left out, so the server refuses it before anything exists; never a "deliberately
  invalid" value, which the server may accept.
- **Shared systems need a yes.** Mark a system `"shared": true` when its write would reach
  something other people use or that lives off this machine (a remote repo, an API, a mailbox).
  The script skips those writes until you rerun with `--allow-shared "<name>"`, naming only the
  systems whose exact write the user agreed to.
- **"Unreachable" needs a probe.** If you plan around a system you believe can't be reached, give
  it `"unreachable": {"why": "...", "probe": "<command that fails while it is unreachable>"}`. If
  the probe succeeds, the plan is wrong.
- The script runs each command with `bash -eu -o pipefail`, rejects `||`, `; true`, `set +e`,
  `exit 0`, `mkdir` and secrets written into commands (use environment variables), and blanks
  secret-looking output. The report goes into `STATE.md`, so never make a probe print a credential.
  These checks catch slips, not intent: an honest check is still your job.

**Exit 1 means stop.** Send the user every BLOCKERS line with its fix in one message, then wait.
Never work around a blocker: don't create a missing drive's folder, write somewhere else, or switch
accounts. That turns "can't reach it" into silent damage. Paste the report under Evidence in
`STATE.md`. Rerun the preflight at the start of every session that touches a system, and whenever
the plan adds one: it proves access only at the moment it ran.

## 5. Run and resume

1. **Start of every session:** read `AGENTS.md` and `STATE.md`, run the preflight, then take the
   next step from the files, not from memory. Look only inside the project and the systems it
   lists; if something is missing, it is a blocker for the user, not a reason to search elsewhere.
2. **Update `STATE.md` as you go**, not at the end: a session can die at any point.
3. **Evidence, not ticks.** Record the command and its output. A step marked done with no evidence
   is not done: check it again before building on it.
4. **Gates.** Decisions that are the user's go to them in one batch, each with your recommendation;
   run only what they agreed. Before anything that can't be undone, show the exact list of what
   will happen and where each item could still be recovered, and wait for a clear yes to that
   list. "Just finish it" is not that yes. Nothing earlier counts as approval for this step.
5. **Between gates, don't ask "shall I continue?"** Log anything unexpected under Problems found
   with a suggested fix, and keep going unless it blocks the next step.
6. **One writer per shared file.** The main session owns `STATE.md`, manifests and registers.
   Helpers (subagents, parallel workers) each get their own files, a list of files not to touch,
   and the project's never-do rules repeated in their instructions.
7. **If a step would break the end state or a rule in `AGENTS.md`, stop and ask.** The step
   changes, not the rule.
8. **End each session at a clean point:** `STATE.md` current and its next step written, rather
   than half a step done.
9. **Finishing:** check the end state again from scratch (a fresh count, a fresh run), not from
   earlier notes, and give every leftover an owner under Left over.

## 6. Reply

Lead with the bottom line: the shape, the project folder, the preflight result (all proven, or the
blockers and their fixes), and how to carry on ("open a session in `<folder>` and say carry on").
Then list anything left as `TBD` and who has to answer it.
