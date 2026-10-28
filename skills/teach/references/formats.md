# Learning folder formats

Plain Markdown. Dates as YYYY-MM-DD. Keep each file short enough to read at the start of a session.
Write about the learner as "the learner" or "you", never with a guessed he or she.

## MISSION.md

```markdown
# Mission
Started: <date>

## Why
<What the learner will use this for, in their words. The real situation: their job, project or goal.>

## Able to do at the end
<A task they can do and show, not "understand X".>

## Starting point
<What they know already, as they said it.>

## Time
<Minutes per session, how often.>

## Changes
<date>: <old goal> -> <new goal>, on the learner's yes. Record NNNN.
```

Leave out `## Changes` until the mission first changes.

## RESOURCES.md

```markdown
# Resources

| Source | Kind | Covers | Checked | Used in |
| :--- | :--- | :--- | :--- | :--- |
| [<title>](<url>) | <standard, maker's docs, original paper, law, textbook...> | <what, with section numbers> | <read YYYY-MM-DD, or not checked: why> | <lesson numbers> |
```

- One row per source. "Checked" says the page was actually read, and when.
- Primary sources first. A secondary source (a tutorial, a course) earns a row only when it does
  something the primary source can't, and its Kind says "secondary".

## records/NNNN-slug.md

```markdown
# NNNN <what this record is about>
Date: <date>
Lesson: lessons/<file>.html (or "chat" for evidence given outside a lesson)
Revises: <NNNN, and why> (only when it does)

## What stuck
<What the learner can now do or explain.>

## Evidence
<The score, their own words, the task they did. Quote them where possible.>

## Still shaky
<Misconceptions and slips, or "nothing noted".>

## Next
<What this suggests for the next lesson.>
```

When a later record revises this one, add `Revised by NNNN` as the first line under the title. Never
delete or rewrite an old record: the history of what was shaky is how spacing works.

A mission change gets a short record of its own: title `NNNN Mission changed`, then `Date:`,
`## From` (the old goal), `## To` (the new goal, as agreed) and `## Why` (the learner's words).
Records written before it still count: what stuck under the old mission is still what the learner
knows.

## NOTES.md

```markdown
# Notes

- <A preference, with the date it was said.>
- Words we use: <term> (not <other term>).
```

## Lesson file names

`lessons/NNNN-<slug>.html` and `records/NNNN-<slug>.md`, four-digit numbers counting up from 0001,
slug in lowercase with hyphens. Each counts up from its own highest number: a lesson the learner
hasn't reported on has no record yet, so the two numbers drift apart.
