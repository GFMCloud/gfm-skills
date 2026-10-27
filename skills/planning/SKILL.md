---
name: planning
description: Plans a change or new build before work starts (goal, done-check, assumptions, risks, steps) and stops for a yes. Use for "plan this first", "how should we build X?", or before a change that deletes data or touches access, DNS, mail, money or a schema. Not for multi-session work or plan reviews.
metadata:
  status: draft
  codex-check: "pending: not yet tried in Codex; must pass before stable"
---

# Planning

The output is a plan, not the work. **Investigate read-only, write the plan, then hold until the
user says yes. Nothing in the project or any live system changes before that yes**, except
a plan file when step 5 calls for one, and the one exception in step 4.

A wrong assumption costs rework or an outage; a needless question costs the user's attention.
Spend your own effort on reading and checking so that neither happens.

## 1. Size it first

Say in one line which size this is and why, so the user can overrule it.

| Size | Signals | What to do |
| :--- | :--- | :--- |
| Trivial | A typo, a rename or a comment within one file; a few lines with one obvious right form | Two lines, no headings: what changes where, and how you'll check it. If the user asked for a plan, stop there as with any plan (step 4); if they only asked you to do it, do it |
| Standard | Several files, one real design choice, a new internal module; anything touching user input, sign-in, file paths, outside calls or encryption is at least this | Steps 2 to 5 |
| Risky | It deletes, overwrites or expires data; changes who can reach or do what; touches money, secrets, shared infrastructure, DNS or mail, a schema, or a service others rely on | Steps 2 to 5 plus the Risk section. Read `references/risky-changes.md` |
| New build | The thing does not exist yet: a tool, a page, a process, a system | Steps 2 to 5, shaped by `references/new-build.md` |

- **Size by the worst signal.** The smallest edit can do the most harm (a
  deletion flag, a wildcard in an access rule, a dropped filter on a delete). The question behind
  the table: if this goes wrong, does a test tell you, or an alert, a customer or a bill? If not a
  test, it is risky.
- **Too big for one sitting** (days of work, many items, an end that can't be undone weeks away):
  say so and hand it to the long-project skill, which sets up work that spans sessions. This skill
  plans what one session can finish, or the first part of something bigger.

## 2. Investigate before you ask

1. **Read first.** Code, tests, config, the docs, recent commits. Anything you can find in a minute
   is not a question for the user: test framework, layout, conventions, where a value is set.
2. **Check the live system, read-only, when the change touches one.** The repo says what should be;
   the running system says what is. List what exists, show the current config, count the files a
   delete would reach, read the deployed version. Name the account, environment, machine or folder
   you looked at, because planning against the wrong environment does more harm than no plan.
3. **Decide the done-check now** (see Done when in step 3) and, if it only reads, run it once and
   keep its output, with the time, as the baseline. A fix starts by reproducing the fault: run the
   failing case and show it failing.
4. **Never run anything that writes during planning.** No apply, deploy, migrate, delete, send,
   commit, install, or a script whose job is to change things (read it instead). If the only way
   to learn something would change state, don't; make it an assumption.
5. **What you can't reach becomes an assumption marked `unchecked`**, with what you ran to reach it
   and what it printed. Never guess it silently and never ask for a password, key or token. If the
   plan would need a secret in plain text, flag that as a design problem; if you find one already in
   a file, say which file (never the value), treat it as exposed and keep it out of the plan.
6. **Premises from memory, a hand-over note or an earlier summary are assumptions too**, until
   you have checked them against the files or the system.
7. **Contradictions are findings.** When the docs, the code and the live system disagree, say
   which says what. Don't quietly pick one.

## 3. Write the plan

**Trivial change: skip this step.** Write only the two lines from step 1, with no headings.

Otherwise use these headings, in this order. A heading with nothing real under it gets one word:
"none".

**Goal.** The request restated in your words, specific enough to be wrong. If your restatement
is off, this is the cheapest place to find out.

**Done when.** The check that settles it, written so two readers would agree whether it passed:
- a command or an observable result, and the exact output or value that means done;
- the baseline: that check's output now, from step 2 (or "can't run yet: <why>");
- for judgment work with no command (copy, a layout, a design choice): two to five criteria,
  each judged on its own, never one overall score;
- what has to stay untouched throughout ("nothing outside `logs/`").
If no check or criteria can be written, ask the one question that would settle it and stop.
If the work will run unattended or in a loop until the check passes, add a stop rule (for example
"stop after 3 attempts") and make sure the check's output gets printed where the loop can see it.

**Questions (0 to 3).** Only where a wrong guess throws work away, not where it means a small
adjustment. Each with the answer you'd pick, so the user can answer "yes to all". "None" is a
good answer; don't pad.

**Assumptions.** Numbered, each one concrete enough that someone could test it and prove it false
("orders never exceed 10,000 rows", not "the code stays maintainable"). Mark each `checked: <command
or file>` or `unchecked`. Cover what the change touches: data shape and volume, what happens on
failure or partial completion, who calls this, concurrency and reruns, environment, and tests.

**Risk** (risky changes). What is deleted, replaced or exposed, named and counted ("13 of the 20
backup files", not "some old files"); how to undo it, or "no undo" in plain words; and drift
between the repo and the live system that you found.

**Steps.** Numbered, in working order. Each names the file, resource or system it touches, what
changes there, and how that step will be checked. Order them so each step can be checked, and
backed out, on its own. For a fix, step 1 is a test that fails before the fix; for a refactor, the
tests pass before and after and no behaviour changes. If the project has no runnable test, say so
and name the check you will use instead. Mark the step that needs the user (a deploy, a delete, a
send) as a gate; if the user carries out every step, mark only the ones that can't be undone.

**Not doing.** What is deliberately out of scope or left for later.

**Rejected.** Each real alternative you weighed and why you didn't pick it, in a few words. If
nothing is listed here, other options probably weren't considered.

Before you show it, check the plan against itself and fix what fails:
- every step names a path, resource or system; a step without one is a wish;
- every step says how it is checked; tests to be added and gaps left untested are both named;
- no step depends on a later one;
- no value is typed in that the project or environment already defines (paths, limits, names);
- the unhappy path is covered: what each risky step does if it stops halfway, times out or errors.

## 4. Stop

End the turn with the plan and one line asking for a yes or for changes to any answer. Do not
start implementing in the same turn, even if the plan looks obvious.

One exception: the user said "plan it and then do it" (or "just do it") and the change is trivial or
standard with no step marked as a gate. Then show the plan and carry it out in the same turn under
step 6. A risky change, and any gate, still waits for a yes.

## 5. Where the plan lives

In the reply. Also save it as `PLAN.md` in the project root (or the path the user names), but only
when the user asks for a file or someone else will carry it out.
That file is the only thing you write before the yes. If one already exists, show what you would
change rather than overwriting it. In an agent's own plan mode, follow this skill inside it and put
the plan where plan mode asks for it.

## 6. After the yes

1. Carry out the plan as approved, step by step, running each step's check as you go. If the plan
   came from somewhere else (a `PLAN.md`, a hand-over, another session), first recheck the
   assumptions it marks `checked` and run its baseline: a check you didn't run yourself is
   unchecked.
2. **If an assumption turns out wrong, or the plan stops matching what you find, stop.**
   Say which assumption or step, what you found (with the command and output), and give two or
   three options with your recommendation. Don't swap in another design without saying so: the user
   approved this one, and a silent substitute turns their yes into something they never gave.
3. If the change turns out bigger than its size (a small change turns out to touch something other
   code or people depend on, or starts deleting data), stop, re-size it and re-plan from step 1.
4. At every gate, show exactly what is about to happen and wait for a yes to that list.
5. Finish by running the done-check and showing its real output beside the baseline. A step
   without a run check is not done. Commit or push only if the plan or the user says so, following
   the project's own rules.

## Borders with other skills

- Work that spans many sessions, or a project to resume: the long-project skill.
- An independent review of a plan or decision you already have: the second-opinion skill. For a
  high-stakes plan, suggest it after this one.
- Creating a new repository's skeleton (git, licence, ignore file, agent instructions): the
  project-start skill, once the plan is agreed.
- Making something run on a schedule, a trigger or a loop: the automation skill. This skill can
  write the done-check and stop rule that run will use.
- Shipping to a live environment and checking it afterwards: the deploy-verify skill. Confirming
  something worked: the proof-of-work skill.
- The look of a page or screen: the design skill.
