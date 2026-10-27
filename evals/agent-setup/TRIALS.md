# Trials: agent-setup

House rule 8: tried in Claude Code (Haiku, Sonnet, Opus) and in Codex before `stable`.

| Agent | Eval cases | Triggers | State |
| :--- | :--- | :--- | :--- |
| Claude Code | Opus 6 of 6 (5 cases plus local-note). Sonnet 6 of 6. Haiku 4 PASS (rule-both, force-push, audit, no-prompts after the description named "permission prompts"), new-skill PARTIAL (loaded only on description 3, then asked instead of resolving the overlap), local-note MISS (not loaded; made the very `CLAUDE.local.md` the case guards against) | Haiku should 4 of 4 and near-miss 4 of 4; Sonnet should 4 of 4 and near-miss 4 of 4 (near-misses went to `intake`, `project-start`, `retro` or nothing) | **draft: Claude Code passed, Haiku gaps open** |
| Codex | not run | not run | **pending** |

`scripts/inventory.py --selftest` holds the script's own fixtures (23 checks, each able to fail,
including malformed settings, `CLAUDE_CONFIG_DIR`, `AGENTS.md` read directly by Claude Code, the
TOML fallback, and a clean set-up that must raise no FAIL or WARN).

## Workspaces (all demo material)

Every run gets a stand-in home folder inside its workspace, and every prompt says the real
`~/.claude`, `~/.codex` and `~/.agents` config must not be read or written (reading the files of a
loaded skill is fine), that no codex command may call a model or contact OpenAI, and that any codex
command runs only with `CODEX_HOME` set to a new empty folder inside the workspace. Without that,
even `codex --version` or `codex execpolicy check` writes runtime files into the real `~/.codex`.
Check the real config folders are unchanged after each wave.

Cases: copy each case's `setup` folders keeping their names below `files/<case>/`, then run
`sh evals/agent-setup/prepare.sh <case-id> <workspace>` for cases marked `prepare: true`.

Triggers, in order:

| Prompt | Workspace |
| :--- | :--- |
| commit-message rule in kiln-log | `files/triggers/commit-rule/`, then `prepare.sh trigger-commit-rule` |
| allow npm test | `files/triggers/allow-tests/` |
| changelog skill | `files/triggers/changelog/` |
| which skills overlap | `files/audit/`, then `prepare.sh trigger-overlap` |
| skill pack worth installing (near-miss) | `files/triggers/pack/` |
| new repo for recipe scaler (near-miss) | `files/triggers/recipe/` |
| explain garden-bot AGENTS.md (near-miss) | `files/triggers/explain/` |
| learn from incident (near-miss) | `files/triggers/incident/` |

Case `local-note` uses `files/local-note/`, then `prepare.sh local-note`.

## Codex runs still owed

No Codex runs yet (the allowance is used up until 2026-11-02; each batch needs the maintainer's OK
on a run count). At minimum: `force-push` (including whether `codex execpolicy check` runs),
`rule-both`, `local-note`, `audit`, one "should" trigger and one near-miss, each with `HOME` and
`CODEX_HOME` pointed inside the workspace. Then set `metadata.codex-check` to `pass` and `status` to `stable`.

## Open from the trials and review

- Haiku did not load the skill for "add a note just for me in Claude Code" (`local-note`), the one
  request where the skill prevents real harm (a bare `CLAUDE.local.md` hides `AGENTS.md` from
  Claude Code). At the next description change, add words for a personal `CLAUDE.local.md` note and
  rerun `local-note` on Haiku plus all near-misses.
- Haiku loaded the skill for "make me a skill" only on the third description.
