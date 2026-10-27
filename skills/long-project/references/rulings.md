# Rulings

A register of decisions that cost something to work out and that a later session would otherwise
work out again or break: "tool A is faster than B here, fall back to B on errors".

## What belongs here

| Kind | Test | Where it goes |
| :--- | :--- | :--- |
| Preference | No evidence could change it ("use British spelling") | Stays in the instructions file |
| Ruling | Measured, could be proven wrong, can go stale | A file in `rulings/` |
| Lesson from an incident | Learned the hard way; doesn't expire | A file in `rulings/`, with the incident as evidence and "none" as what would prove it wrong |

If nothing in scope is a ruling, say so and don't set up an empty register.

## Files

```text
<location>/rulings/
├── INDEX.md       one row per ruling file: slug, the ruling, recheck by
└── <slug>.md      one file per ruling
```

`INDEX.md` is the only list. It lists exactly the files present; nothing else repeats the count.

A register inside an existing long project uses that project's `AGENTS.md`, `STATE.md` and
preflight. A register on its own needs only these files until a recheck touches a system (a data
folder, a database); then it gets `preflight.json` and `tools/preflight.py` like any project.

## A ruling file

```markdown
# <the ruling, one imperative line>
Evidence: <what was measured, how, when, with the numbers>
Wrong if: <what result would overturn it, or "none: lesson from an incident">
Recheck: <the command or test that measures it again>
Recheck by: <date>
Source: <where it came from: a run, an incident, a file>
```

All five fields are filled; a ruling without evidence is a preference.

## Moving rulings out of an instructions file

Propose, don't edit. Write the new ruling files and a short list of the lines that would leave the
instructions file, and hand that to the user to apply. Never edit the user's instructions file as a
side effect.

## Rechecking

When asked to recheck (or when a project session starts and a "recheck by" date has passed), run
each ruling's Recheck and compare against Evidence and Wrong if. Report the rulings whose test
fired or whose date passed. Don't rewrite a ruling yourself: changing one is the user's decision,
recorded as a new version with the new evidence.
