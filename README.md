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
| `design` (draft) | Designs a new page, screen or form in your brand, redesigns one that looks dated or breaks on phones, or critiques one | Writes or edits the page files in your project and runs three small Python scripts (brand lookup, page check, and a dealer that picks art directions from a bundled library when you have no brand). The page check can take screenshots with a local headless browser. Pages it makes may load fonts from Google Fonts or Fontshare; it searches open picture collections and downloads a picture only on your yes |
| `proof-of-work` (draft) | Proves work is done by running it, reports what was checked and what was not, and lints a message before you send it | Runs the checks the work needs (tests, the script, a page load) and one small Python linter. Changes nothing unless you ask |
| `long-project` (draft) | Sets up and resumes work that takes many sessions (a phased project, a sweep over many items, experiments, a register of decisions, or a map of open decisions settled one per session) in files any session can pick up, and first proves it can read and write every system the work needs | Writes a project folder of plain text files and copies in one small Python script that runs the read and write checks listed for the project (each write check, as the skill writes them, makes the smallest test write, such as a tiny file, and removes it). Asks before writing to anything shared or off your computer, and never deletes without your yes to the exact list |
| `research` (draft) | Answers questions about the world as it is now, and rechecks whether claims in a brief, plan or doc still hold today, with dated primary sources and a verdict per claim | Searches the web and reads pages. May run a command on copies in a scratch folder to test how a tool behaves, then removes the folder. In deep mode writes a notes file. Installs and sends nothing |
| `planning` (draft) | Plans a change or a new build before any work starts: checks the code and the live system read-only, then gives the goal, a runnable done-check, assumptions, risks and steps, and waits for your yes | Reads files and runs read-only commands (listings, `git log`, the project's tests). Writes nothing before your yes, except a `PLAN.md` if you ask for one or someone else will carry the plan out |
| `project-start` (draft) | Starts a new repo, turns a loose folder or a local repo into one ready for GitHub, or sets up a Claude Project from a brain dump, with a secret scan before the first commit | Writes the starting files (`.gitignore`, README, `AGENTS.md`, a one-line `CLAUDE.md`, a licence if public), runs `git init` and the first commit, and adds a pre-commit hook plus a small Python secret scanner to the project. Runs gitleaks too if you have it. Creates a GitHub repo only after you say yes to its exact name; never pushes otherwise |
| `deploy-verify` (draft) | Deploys a change to staging (production only on your say), checks it at the address people use, and fixes and redeploys until it works or a stop rule says hand back; also writes smoke tests, reviews a site before launch and moves a site to a new host without breaking DNS | Runs your project's own build and deploy commands for the target you name, and two small Python scripts that only read from the site (GET and HEAD). Keeps rollback copies in `.deploy-check/` in your project. Changes DNS, production or an old host only after you say yes |
| `automation` (draft) | Builds jobs that run without you watching: a schedule, a watch that tells you only when something changes, or an overnight loop that keeps fixing until the tests pass. Each job has limits, writes a status on every run and is proven before hand-over | Writes the job as files in your project (a script, a scheduler file such as a launchd plist, install steps) and runs it by hand to prove it, on copies where it would change things. Never installs, schedules or loads anything: you turn it on with the commands it gives |
| `agent-setup` (draft) | Changes your own agent setup for Claude Code and Codex: adds rules to `AGENTS.md` or `CLAUDE.md`, makes or fixes skills (with evals), tightens skills and instruction files (cuts lines that change nothing, turns bans into the behaviour wanted and vague steps into checks), allows or blocks commands, adds guard hooks, and audits what you have installed | Runs one small read-only Python script that lists your instruction files, skills and settings and flags problems (it never prints a setting's value). Tries each change in a scratch copy first, asks before anything that lets the agent do more without asking, and ends with the exact undo. Writes only the files the change needs |
| `asset-review` (draft) | Reviews a sell sheet, one-pager, case study, cold email, talk track or deck copy as its buyer and a sales leader would: a verdict, the one change that matters most, and rewrites of the weak lines, checked against your brand's voice and banned claims if you have them | Reads the asset and runs one small Python script (brand lookup). Changes no files unless you ask; rewrites never add customers or numbers the asset doesn't have. No outside requests |
| `doc-digest` (draft) | Turns a long PDF, Word file or slide deck into a summary, a notes file or a folder of knowledge-base files, with a page reference for every fact, the source's own problems flagged, and every number checked against the source | Reads the documents and runs two small Python scripts (text extraction, a number check), using pdftotext if you have it. Writes the notes or knowledge files in your folder and a scratch copy of the text it deletes afterwards. No outside requests |
| `model-choice` (draft) | Picks the model and effort level for a task, subagent or project in Claude Code or Codex, says whether a job is worth a multi-agent workflow, runs bulk mechanical work on a local model, and sets up a split where a strong model reviews and plans and a cheaper one carries it out | Reads the task and a dated model list inside the skill, and rechecks the list on the web when it is over a month old. For local work, runs one small Python script that talks only to a model server on this machine and writes results beside your task; never installs, downloads or starts anything, and stops for a yes after a sample. A split writes one improvement-plan file into the project |
| `handoff` (draft) | Writes a handoff file that a new session, another agent or a person can pick up from, with each checkable fact recorded by running a read-only command, and re-runs those checks when a session resumes from it; also prepares a copy of a repo to give someone else without your personal data | Writes the handoff file in your project and runs only read-only commands it knows (anything else waits for your yes). On resume it writes a small marker file beside the handoff. For a shared repo it writes a new copy beside the original, never changes the original, and creates nothing on GitHub without your yes to the exact name |
| `data-matching` (draft) | Works out which records in two lists (or one) are the same customer, supplier or person when names and IDs don't line up, and writes a mapping file you can reuse next month | Runs a Python script (standard library) on the files you name and writes its results to a new folder beside them. Never changes your files and never goes online |
| `brag` (draft) | Makes a 15 to 25 second launch video of something you built, from its own screens and words, with music, sound effects, a poster frame and a caption to post | Reads your project after a script has set aside secrets, config and data files; writes a `brag-output/` folder in the project. Renders with Hyperframes (asks before `npx` downloads it) or with a bundled script that drives a headless browser and ffmpeg. Never posts or uploads |
| `scrollback` (draft) | Builds, restyles or checks pages in one fixed dark, monospace "terminal" design system for status pages, dashboards, invoices, changelogs and docs, and draws charts on them its way (one colour, no legend) | Writes the page you ask for in your project, plus a `.scrollback-check/` folder of screenshots you can delete. Its checker runs Python (standard library; playwright for screenshots) and blocks every outside request. Pages it makes load a monospace web font from Google Fonts when someone opens them |
| `jev` (draft) | Finds where TypeSafe's Jev model (cheap yes/no, pick-one and score judgments) could replace an LLM call or a review step in your project, says plainly where it can't, and builds a checked Jev step scored against decisions you already made | Reads your project and copies three Python files into it. Sends data to TypeSafe only with your key set, only data your data rule allows, and only when you run the evaluation; everything else works offline |
| `grill` (draft) | Interviews you about a design, decision or idea in rounds until every decision is settled: all the questions that can be asked now at once, each with a recommended answer you can accept with "yes", then a list of what was decided | Reads the files you point it to and may start a subagent to look facts up. Writes nothing until you confirm the decision list, and then only if you ask for a file |
| `debug` (draft) | Finds and fixes the cause of a reported fault: first a command that shows the failure, then ranked causes tested one at a time, then the fix with a regression test where the fault really happened | Runs the project's own commands and tests, edits the code and tests, and keeps scratch files in `.debug/` (removed at the end). Checks out old commits only in a scratch worktree; calls no live service |
| `wizard` (draft) | Writes one script that walks you through the console steps only you can do (DNS records, dashboards, creating API keys, CI secrets, a cutover): it opens each page, says what to click, takes secrets with hidden typing straight into the macOS keychain or 1Password, asks for a typed yes before anything that can't be undone, and ends by listing what it did | Reads your project (key names only from .env files, never values) and writes one bash script into it. Never runs the script: you do, in your own terminal |
| `teach` (draft) | Teaches you one topic over several sessions: keeps a learning folder of why you are learning it, checked primary sources and what has stuck, and writes one short HTML lesson per session with one win, recall practice and one source to read | Writes only inside the learning folder you name (never your project folder unless you say so) and runs one small Python check on each lesson. Reads the web through the research skill to check sources. Never opens, sends or publishes anything; prints the lesson's path for you to open |

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

The `design` skill is written fresh in this library's own words, except its art-direction library
(`skills/design/references/directions.json`), which is cut from
[taste-skill](https://github.com/Leonxlnx/taste-skill) by Leonxlnx under the MIT licence (see
`THIRD_PARTY_NOTICES.md`). Its approach was also inspired by taste-skill,
[emil-design-eng](https://github.com/emilkowalski/skills) by Emil Kowalski, and Anthropic's
[frontend-design](https://github.com/anthropics/skills) skill, from which no text is included.

## Licence

MIT (see `LICENSE`). Skills that include text from other projects keep those projects' licences in
their own folders; see `THIRD_PARTY_NOTICES.md`.
