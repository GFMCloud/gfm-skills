# Trials: deploy-verify

House rule 8: tried in Claude Code (Haiku, Sonnet, Opus) and in Codex before `stable`.

Every fixture is DEMO material. The "hosts" are folders served on 127.0.0.1 by `demo_server.py`,
which the person running the trials starts outside any agent sandbox (sandboxes that block local
ports stop both binding and connecting). Trial prompts allow only read-only requests to 127.0.0.1
outside the sandbox. `test_scripts.py` checks both scripts against the fixtures (29 cases); it needs
local ports too.

| Agent | Eval cases | Triggers | State |
| :--- | :--- | :--- | :--- |
| Claude Code | Haiku 5 of 5 and Sonnet 5 of 5 on the first draft; Opus 5 of 5 on the second. After the review fixes, ship-to-staging, smoke-test and host-move (Haiku) and host-move (Sonnet) rerun: all pass | Sonnet 6 of 6 should, 7 of 7 near-miss on the final description. Haiku 6 of 7 near-miss on the final description; should 6 of 6 loaded across both descriptions (two of them reported no TRACE line but followed the skill's report format exactly) | **draft** |
| Codex | not run | not run | **pending** |

Known limits:

- The skill's name contains "verify", which pulls "verify the deploy" requests toward it. On the
  first description Haiku took "The deploy pipeline is green, so we're live, right? Verify it." (a
  proof-of-work trigger); the final description's "Not for confirming a past deploy" stopped that.
- "Plan how we'd move the site to the new host. Don't change anything yet." loads this skill
  alongside planning on Haiku (Sonnet loads planning only); the "Which job is this?" table sends
  "plan it first" to planning.

**Still needed before `stable`: a Codex pass** (at minimum `ship-to-staging`, `staging-unreachable`,
`site-ready`, should triggers 1 and 3, and near-misses 1, 2 and 5), run with the demo servers started
outside the Codex sandbox. Then set `metadata.codex-check` to `pass` and `status` to `stable`.

**2026-10-27, R12 real-task fixes (branch `fix/r12-trial-findings`):** SKILL.md text changed after
real-task trials on private projects (logs kept outside this repo). Earlier counts in this file
predate the change; rerun the triggers and cases before `stable`.
