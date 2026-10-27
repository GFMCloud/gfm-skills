# Trials: model-choice

House rule 8: tried in Claude Code (Haiku, Sonnet, Opus) and in Codex before `stable`.

| Agent | Eval cases | Triggers | State |
| :--- | :--- | :--- | :--- |
| Claude Code | Opus 4 of 4 (post-fix text). Sonnet 4 of 4 (local-offload passed again after the fixes). Haiku: pick-one 2 of 2, breakdown-codex 1 of 1, split-review 1 of 3 (passes on the final description, missed on the first two), local-offload 1 of 3 (see below) | Should: Haiku 5 of 5, Sonnet 5 of 5. Near-miss: Haiku 6 of 6, Sonnet 6 of 6 (to claude-api, second-opinion, planning, intake, or nothing). Final description | done, one Haiku gap |
| Codex | not run | not run | **pending** |

**Haiku gap: local-offload.** On "Tag each message ... keep the messages on this machine; run it
on a local model", Haiku loaded the skill once in three runs (descriptions 1 to 3). The two misses
tagged all 30 messages with a keyword script, the fallback the skill forbids. Tuning stopped after
three descriptions. The trigger prompt "Can a local model on my laptop do it instead of burning my
usage?" loaded it on both models.

**Border with proof-of-work.** "Check the cheaper model's work against the plan" goes to
proof-of-work (Haiku 2 of 2, Sonnet 1 of 1 when it was a case here), which does it well; it is now
near-miss n6, and `references/split.md` step 7 defers to proof-of-work.

Not rerun: the last local.md sandbox sentence ("stop there; don't retry it outside the sandbox"),
added after an Opus run tried a sandbox bypass. Rerun local-offload on Opus at the next change.

Trigger workspace: copy `files/trigger-project/` (all demo files) into the working folder for every
trigger prompt, should and near-miss alike.

**Still needed before `stable`: a Codex pass** (no Codex runs before 2026-11-02). At minimum:
`breakdown-codex` (Codex model names and `-c model_reasoning_effort` from `references/models.md`, no
Claude Code commands), `split-review` (the kickoff is a `codex -m` command), `local-offload` (Codex
has no subagent tool; the run must still check for a server and stop, and may mention
`codex --oss`), one "should" trigger (the Codex jobs prompt) and one near-miss. Then change
`metadata.codex-check` in `SKILL.md` to `pass` and `status` to `stable`.

`references/models.md` dates fast. Recheck it (and these cases' expect lines that name tiers)
whenever a vendor ships or retires a model, and at least monthly.
