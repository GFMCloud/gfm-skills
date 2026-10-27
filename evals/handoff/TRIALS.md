# Trials: handoff

House rule 8: tried in Claude Code (Haiku, Sonnet, Opus) and in Codex before `stable`.

| Agent | Eval cases | Triggers | State |
| :--- | :--- | :--- | :--- |
| Claude Code | Final skill: Opus 4 of 4 (resume after a wording fix). Sonnet 4 of 4. Haiku: write and share 2 of 2 first time; no-files after the "leave checks empty" fix; resume after the "Resuming from this file?" line and the "one question, then stop" fix (it first missed the skill, then asked several questions, then regenerated output before asking) | Haiku should 4 of 4, near-miss 4 of 4; Sonnet should 4 of 4, near-miss 4 of 4 (near-misses went to long-project, project-start, retro or nothing) | **draft: Claude Code passed** |
| Codex | not run | not run | **pending** |

Both scripts carry their own tests: `python3 skills/handoff/scripts/check_claims.py --selftest`
(the read-only guard on 100 commands, and fill, run and take on a scratch project) and
`python3 skills/handoff/scripts/clean_check.py --selftest` (terms in files, names and commit
authors; secret-type files; an unreadable file; a terms file inside the tree).

## How the Haiku resume miss was fixed

On the description alone, Haiku did not load the skill for "Pick up the invoice export work from
the handoff in invoice-tool/" (1 run) and edited code before asking anything. Every handoff this
skill writes now opens with "Resuming from this file? If a skill named `handoff` is available,
load it before reading on." The resume fixture stands for a file the skill made, so it has the
line, and the resume case and trigger now measure the line, not the description alone. With it,
Haiku loaded the skill in 4 of 4 runs.

## Known limits

- The read-only guard trusts its lists. It refuses what it knows can write, run a program, send a
  file or read a secret-type file, and lets through the read-only commands it knows; a command it
  doesn't know needs a yes. A recursive `grep -r . .` can still print a secret from a file with an
  ordinary name; the output check catches common secret shapes only.
- `git diff` and `git show` still run textconv filters set in the repository's own config. That
  only matters for a hostile repository.
- clean_check matches terms as written, ignoring case. A name split across lines or spelled another
  way needs its own line in the terms file.

## Workspaces (all demo material)

Cases: copy each case's `setup` files keeping their folder names below `files/`, then run
`sh evals/handoff/prepare.sh <case-id> <workspace>` for cases marked `prepare: true`. It writes the
git history, the fake key and the file times inside the workspace only. `write-mid-task` moves
`SESSION-NOTES.md` to the workspace root, since it stands for the conversation, not a project file.

Triggers, in order:

| Prompt | Workspace |
| :--- | :--- |
| context is getting long | `files/price-alerts/` plus `prepare.sh trigger-write` |
| switching to Codex | `files/price-alerts/` plus `prepare.sh trigger-write` |
| pick up from the invoice handoff | `files/invoice-tool/` plus `prepare.sh trigger-resume` |
| friend wants to run fantasy-draft | `files/fantasy-draft/` plus `prepare.sh trigger-share` |
| docs-old move over several weeks (near-miss) | `files/near-miss/docs-old/` |
| check draft-message.md (near-miss) | `files/near-miss/draft-message.md` |
| what went wrong in the session (near-miss) | `files/near-miss/notes/` |
| git repo with README and AGENTS.md (near-miss) | `files/near-miss/docs-old/` plus a one-line `notes.md` |

## Codex runs still owed

No Codex runs yet (the allowance is used up until 2026-11-02; each batch needs the maintainer's OK
on a run count). At minimum: `write-mid-task`, `resume-mismatch`, one "should" trigger and one
near-miss. Then set `metadata.codex-check` to `pass` and `status` to `stable`.
