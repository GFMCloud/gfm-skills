# gfm-skills

A small library of skills for **Claude Code** and **Codex**. Each skill is a folder with a
`SKILL.md` file that tells the agent how to do one job well. The agent loads a skill only when your
request matches it.

## Install

You need `git`. On macOS or Linux:

```sh
git clone https://github.com/GFMCloud/gfm-skills.git ~/gfm-skills
sh ~/gfm-skills/install.sh
```

This links each skill into `~/.claude/skills` (Claude Code) and `~/.agents/skills` (Codex). To update
later, run `git -C ~/gfm-skills pull`. To remove the links, run `sh ~/gfm-skills/install.sh --uninstall`.
If the install created one of those folders for the first time, restart Codex or run `/reload-skills`
in Claude Code.

**No git, or a locked-down laptop (including Windows)?** Download the ZIP from the GitHub page
(Code, then Download ZIP), unzip it, and copy the folders inside `skills/` into
`~/.claude/skills/` (Claude Code) or `~/.agents/skills/` (Codex). On Windows, `~` is your user folder,
for example `C:\Users\you`. A copied install doesn't update itself; download again to update. Put
your brand in `.agents/brand/` in your project or in `~/.agents/brand/`, not inside the copied
skill, because copying a newer version over it would replace it.

## The skills

| Skill | What it does | What it does on your computer |
| :--- | :--- | :--- |
| `doc-vs-reality` (draft) | Checks whether a README, spec or status note still matches the files or system it describes, and lists every mismatch with evidence | Reads files and runs read-only commands such as `ls` and `git log`. Changes a document only if you ask it to fix one |
| `diagrams` (draft) | Builds a clickable HTML diagram of a system or data flow, with highlightable paths and your brand | Copies a template into a new HTML file and runs two small Python scripts (brand lookup, validator). No outside requests |

Skills marked `draft` in their `SKILL.md` work but are still being tested.

## Your own brand

Skills that make pages, diagrams or decks can use your brand colours and style notes without you
editing the skill. They look in this order and use the first one they find:

1. `.agents/brand/` in the project you're working in (a company repo can ship its brand here).
2. `local/` inside the skill's own folder in your copy (never shared, ignored by git).
3. `~/.agents/brand/` in your home folder (one brand for every skill on your computer).
4. The skill's built-in defaults.

Put a `tokens.json` there, for example `{ "primary": "#0f766e" }`, and optionally a
`guidelines.md` with tone and style notes. The skill tells you which one it used.

## Contributing

See `AGENTS.md` and `docs/house-rules.md`. Before a change: `uv run tools/check_skills.py` and
`uv run tests/run_fixtures.py`.

## Licence

MIT (see `LICENSE`). Skills that include text from other projects keep those projects' licences in
their own folders; see `THIRD_PARTY_NOTICES.md`.
