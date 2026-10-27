# Evals for a skill or a rule

A run that passed once says it passed once. Agents vary run to run, so the question is how often it
passes, and whether it beats not having the skill or rule at all.

## Write them before the change

Keep evals beside the thing they test, versioned with it (for a skill: `evals/<name>/` next to the
skill folder, outside it, so they don't install with it).

- **Trigger prompts** (skills only): at least three that should load the skill and three near-misses
  that share its words but are another job. Give each a folder with real material; an empty folder
  makes models ask instead of acting.
- **Cases**: two or three realistic requests, each with `expect` lines a reviewer can check without
  asking the author ("names the file and line", not "is helpful").
- At least one case where the right answer is to stop, refuse or ask (a request to widen access, a
  missing input). Happy-path-only evals pass skills that do harm.
- Keep one case back: don't tune against it, and run it last.

```yaml
cases:
  - id: <short-id>
    prompt: <the request, word for word>
    setup: [files/<id>/...]      # demo material, labelled demo in the files
    expect:
      - <one observable thing>
should: [<prompt>, ...]
should_not: [<prompt>, ...]
```

## Run them

1. **Isolate.** Each run in a fresh session and a fresh copy of the workspace. Point `HOME` (and
   `CODEX_HOME`, `CLAUDE_CONFIG_DIR`) at a folder inside the workspace when the task touches agent
   config, and say in the prompt that the real home must not be touched. Leave out the user's own
   instruction files where the agent allows it, or a global rule may do the skill's job.
2. **Baseline.** The same prompts without the skill (or rule). Same model, same files.
3. **With it.** Install where the trial can see it, confirm it is listed before the first run (ask
   the agent "is a skill named X available?"), then run.
4. **Repeat.** Each case at least twice per model; three times when the result will decide something.
   Record every run, failures included. One run has no rate.
5. **Grade from files.** Read what the run wrote and diff the workspace against the original, not
   the run's own summary. A run that does the right thing without loading the skill is a miss for the
   skill: it shows the baseline is already good.

## Graders

1. **Script** where the check can be stated mechanically: a command's exit code, a file exists, a
   pattern is present or absent. Make each script fail once on purpose to prove it can.
2. **Model** for judgment: a separate run with a written rubric, not told which arm it is grading.
   It is a second opinion, not a measurement.
3. **Human** for anything that widens permissions, touches credentials or weakens a safety check.

## Report

```
Evals: <skill or rule>   runs per case: <k>   models: <list>
| Case | Baseline | With it | Notes |
| <id> | 1 of 3   | 3 of 3  | <what differed> |
Triggers: should <n of n>, near-miss <n of n> (where the misses went)
Held back: <case> <result>
Not checked: <what no eval covers>
```

A difference of one run in three is noise. Call it a gain only when it holds across runs and models,
and when added text alone (a longer prompt) wouldn't explain it.

## When the change fails its evals

Fix and rerun the cases that failed and all near-misses after a description change. After about
three tries on the same miss, stop tuning and report it as open, with the runs.
