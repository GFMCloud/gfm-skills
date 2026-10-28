# gfm-skills: rules for agents working in this repo

This is a **public** skill library for Claude Code and Codex. Anything committed here is visible to
everyone, including in branches and pull requests.

## Before every commit

0. Once per clone: `sh tools/install-hooks.sh`. The hooks run the checks on every commit and push;
   the pre-push hook needs `~/.config/gfm-skills/deny.txt` (see `docs/house-rules.md`). Pull
   requests from forks never see the CI secret, so these hooks matter.
1. Run the checks: `uv run tools/check_skills.py` and `uv run tests/run_fixtures.py`. Both must pass.
2. Never commit anything under `skills/*/local/`. That folder holds a user's own brand material.
3. Never write employer names, work repo names, work tool names, home-folder paths or personal
   details into this repo. Describe them by type.
4. Text borrowed from another project keeps its licence file in the skill's folder and gets a row in
   `THIRD_PARTY_NOTICES.md`.

## Writing a skill

Follow `docs/house-rules.md`. In short: one folder per skill under `skills/`, a `SKILL.md` with
`name` and `description` frontmatter only (plus `license`, `compatibility`, `metadata` when needed),
a description of at most about 250 characters in the third person that says what the skill does,
when to use it and what it is not for, and a body under 500 lines. A skill is `draft` until it has
evals in `evals/<name>/` and has been tried in both Claude Code and Codex.

Before adding a new skill, decide whether it belongs in one that exists. For a skill from another
pack, run `intake`; for an idea, follow agent-setup's "Before writing" check. If an existing skill
produces the same kind of output, fold the new job into it or improve its description instead of
adding a competitor. A new skill merges as `draft`; house rule 8 decides when it is `stable`.
