# Trials: project-start

House rule 8: tried in Claude Code (Haiku, Sonnet, Opus) and in Codex before `stable`.

| Agent | Eval cases | Triggers | State |
| :--- | :--- | :--- | :--- |
| Claude Code | Final skill: Opus 5 of 5. Sonnet 5 of 5 and Haiku 5 of 5 after the fixes (both first missed `chat-project` until the description named it). Haiku loaded `local-repo-to-github` 4 of 5 times; the one miss came before the description said "local repo" | Haiku should 3 of 3, near-miss 4 of 4; Sonnet should 3 of 3, near-miss 4 of 4 (near-misses went to `init`, `long-project`, `planning` or nothing) | **draft: Claude Code passed** |
| Codex | not run | not run | **pending** |

`secret_scan.py --selftest` holds the script's own fixtures (25 checks, each able to fail), with
its fake secrets built at run time so none is stored in this repo.

Known limits, from an independent review (not fixed yet): the `_auth=` and `Bearer` patterns flag
placeholder lines, such as a basic-auth setting holding a user and the word password, or a Bearer
header followed by a your-token-here placeholder (this file once tripped the first one); names like
`secret_name = "..."` are flagged; `.env.example` values are scanned like any file; test values
such as `"test-token-12345"` block; camelCase names such as `githubToken = '...'` are missed; a
Python 2 `python` with no `python3` makes the hook fail with no hint. False alarms fail closed and
go to the user to decide; the hook also runs gitleaks when installed.

## Workspaces (all demo material)

Cases: copy each case's `setup` files keeping their folder names below `files/<folder>/`, then run
`sh evals/project-start/prepare.sh <case-id> <workspace>` for cases marked `prepare: true`. It
writes the fake secrets and git history inside the workspace only.

Triggers, in order:

| Prompt | Workspace |
| :--- | :--- |
| recipe scaler | `files/triggers/recipe/` |
| scans/ folder | `files/triggers/scans/` |
| habit tracker set-up | `files/triggers/habit/` |
| CLAUDE.md for an existing repo (near-miss) | `prepare.sh trigger-existing-repo` |
| wiki migration across sessions (near-miss) | `files/triggers/wiki/` |
| commit what I've changed (near-miss) | `prepare.sh trigger-uncommitted` |
| plan for the habit tracker (near-miss) | `files/triggers/habit/` |

## Codex runs still owed

No Codex runs yet (the allowance is used up until 2026-11-02; each batch needs the maintainer's OK
on a run count). At minimum: `folder-with-secrets`, `local-repo-to-github`, `new-python-tool`, one
"should" trigger and one near-miss. Then set `metadata.codex-check` to `pass` and `status` to
`stable`.
