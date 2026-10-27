# Experiment

Work with no finish line: tuning a model, testing ideas against data, long analysis. The risks are
rerunning an idea already killed and explaining a result after seeing it.

## Files

```text
<project>/
├── AGENTS.md          what this is, rules, how to resume, never-do list
├── CLAUDE.md          one line: @AGENTS.md
├── STATE.md           resume point (template in SKILL.md); Progress points to REGISTER.md
├── preflight.json     systems the work touches (data, compute, where results go)
├── HOLDOUT.md         the fixed data or test every prediction is scored against
├── REGISTER.md        one row per idea, append only
├── dead-ideas.md      killed ideas and why
└── runs/
    └── 0001-<slug>.md one file per run
```

## HOLDOUT.md

What results are scored against (a data slice, a test set, a fixed scenario list), how it is
frozen (a file and its checksum, a commit), and since when. Freeze it before the first run: a
holdout that can change is just more data being fitted. If there is none yet, say so and make
settling it the first step; until then no run is scored.

## REGISTER.md

| id | idea | prediction | status | run |
| :--- | :--- | :--- | :--- | :--- |

Append a row per idea. Change only `status` (`open`, `tested`, `killed`) and `run`. Never edit a
prediction after a result exists.

## dead-ideas.md

| idea | why it was killed | run or source |
| :--- | :--- | :--- |

Before adding an idea, read this list. If the new idea matches a dead one, even in other words,
tell the user and ask before running it. When seeding from old notes, copy the reason given; if
none is given, write "reason not recorded".

## A run file

```markdown
# Run 0003: <slug>
Parent: run 0002 | none
Idea: <register id>
Prediction: <the number or outcome expected, written before running>
Config: <exact settings, data version, code commit, command>

## Result
<filled in only after running, from output you read>
Verdict: supports | refutes | no answer
```

## Rules

- **Prediction first.** Idea, Prediction and Config are saved before the run starts. A run file
  with an empty Prediction gets no Result.
- **Read the output, not the status.** Exit 0 means it ended, not what it measured.
- **A run that answered nothing** (crash, out of memory, timeout) is repaired and rerun in the same
  file. After two such runs in a row, stop and ask.
- **A run that answered is frozen.** A follow-up is a new run file naming it as Parent. A
  disappointing number is a result, not a reason to rerun.
- **Build on the winner.** Options tried side by side share a parent; the next round hangs off the
  best of them, not off the baseline again.
- After three runs in a row that fail to beat the current best, stop and write up where things
  stand.
- When a run refutes an idea, set it to `killed` and add a row to `dead-ideas.md`.
