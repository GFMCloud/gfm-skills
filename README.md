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
in Claude Code. A Claude Code session can take a little while to notice new skills, so start a new
session if one doesn't show up straight away.

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
| `second-opinion` (draft) | Gets independent opinions on a decision or a draft from reviewers who never saw your conversation, and shows where they disagree | Starts a few extra agent runs (subagents), which uses more of your plan's allowance. Reads the files you point it to; sends nothing |
| `intake` (draft) | Reviews a repo, tool, skill pack or article someone shared and gives a verdict on adopting it | Reads the files, may make a shallow `git clone` into a scratch folder. Never runs the source's scripts or installs anything |
| `retro` (draft) | Runs a short retrospective after a piece of work and says where each lesson should go | Reads the session record and `git log`. Proposes edits to your instructions; changes nothing without your OK |
| `de-ai` (draft) | Edits text that reads machine-written into plain text, keeping every fact | Edits only the text you give it |
| `decks` (draft) | Plans a slide deck, builds it as one HTML file in your brand (prints to PDF), or reviews slides you already have | Copies a template into a new HTML file and runs two small Python scripts (brand lookup, validator). No outside requests |
| `design` (draft) | Designs a new page, screen or form in your brand, redesigns one that looks dated or breaks on phones, or critiques one | Writes or edits the page files in your project and runs two small Python scripts (brand lookup, page check). The page check can take screenshots with a local headless browser. No outside requests |
| `proof-of-work` (draft) | Proves work is done by running it, reports what was checked and what was not, and lints a message before you send it | Runs the checks the work needs (tests, the script, a page load) and one small Python linter. Changes nothing unless you ask |
| `long-project` (draft) | Sets up and resumes work that takes many sessions (a phased project, a sweep over many items, experiments, a register of decisions) in files any session can pick up, and first proves it can read and write every system the work needs | Writes a project folder of plain text files and copies in one small Python script that runs the read and write checks listed for the project (each write check, as the skill writes them, makes the smallest test write, such as a tiny file, and removes it). Asks before writing to anything shared or off your computer, and never deletes without your yes to the exact list |

Skills marked `draft` in their `SKILL.md` work but are still being tested. All the skills above have
passed their Claude Code trials but **still need a Codex pass** before they can be marked stable
(see `evals/<skill>/TRIALS.md`).

## Your own brand

Skills that make pages, diagrams or decks can use your brand colours and style notes without you
editing the skill. They look in this order and use the first one they find:

1. `.agents/brand/` in the project you're working in (a company repo can ship its brand here).
2. `local/` inside the skill's own folder in your copy (never shared, ignored by git).
3. `~/.agents/brand/` in your home folder (one brand for every skill on your computer).
4. The skill's built-in defaults.

Put a `tokens.json` there, for example `{ "primary": "#0f766e" }`, and optionally a
`guidelines.md` with tone and style notes. The skill tells you which one it used.

## Suggested agent rules

Some habits apply to every task, so they work better as a line in your `AGENTS.md` or `CLAUDE.md`
than as a skill. [`docs/agent-rules.md`](docs/agent-rules.md) has them, ready to paste.

## Contributing

See `AGENTS.md` and `docs/house-rules.md`. Before a change: `uv run tools/check_skills.py` and
`uv run tests/run_fixtures.py`.

## Credits

The `design` skill is written fresh in this library's own words. Its approach was inspired by
[taste-skill](https://github.com/Leonxlnx/taste-skill) by Leonxlnx,
[emil-design-eng](https://github.com/emilkowalski/skills) by Emil Kowalski, and Anthropic's
[frontend-design](https://github.com/anthropics/skills) skill. No text from them is included.

## Licence

MIT (see `LICENSE`). Skills that include text from other projects keep those projects' licences in
their own folders; see `THIRD_PARTY_NOTICES.md`.
