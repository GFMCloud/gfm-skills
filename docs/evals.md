# Evals

Each skill keeps its evals in `evals/<skill-name>/`, outside the skill folder, so they never ship
inside an install. A `stable` skill needs both files below; the checker enforces the shape
(house rule 7).

## cases.yaml

At least three cases. Each one is a realistic request and what a good answer must do.

```yaml
cases:
  - id: drifted-readme            # short, unique
    prompt: Does the README still match the code in this folder?
    setup: [files/drifted-readme/README.md]   # optional; paths are relative to evals/<skill>/
    expect:                       # each line is one thing a reviewer checks in the answer
      - Names the wrong install command and the line it is on
      - Says which claims it could not check
    grader: human                 # human (default) or contains (every expect line appears verbatim)
```

## triggers.yaml

At least three prompts that should load the skill and three near-misses that should not. A
near-miss uses the same words for a different job.

```yaml
should:
  - Check whether this README is still accurate
should_not:
  - Write a README for this project
```

## How to run them

There is no runner yet. Run each case by hand in a fresh session of each agent (Claude Code with
Haiku, Sonnet and Opus, and Codex), with only this library installed, and note the result next to the
case. Record a baseline without the skill first, so a gain can be told apart from noise.
