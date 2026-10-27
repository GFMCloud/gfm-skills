---
name: agent-setup
description: Use when asked to make a skill, add a rule to AGENTS.md or CLAUDE.md, allow or block a command, cut permission prompts, add a guard hook, or check which installed skills overlap, in Claude Code or Codex. Tests changes before they go live. Not for others' packs, retros, new repos or schedules.
metadata:
  status: draft
  codex-check: "pending: not yet tried in Codex; must pass before stable"
---

# Agent setup

Changes the user's own agent setup (instructions, skills, permissions, guard hooks) for Claude Code,
Codex or both, so the change does what was meant, in the right place, for every agent the user runs.
`<skill>` below means this skill's own folder; running its script and reading its references is part
of using it, even when the folder sits under `~/.claude/skills` or `~/.agents/skills`.

**Three hard rules.**
1. Test before it goes live. A settings file, hook, rule file or skill is first tried somewhere it
   can't hurt: a copy of the file in a scratch folder, or a stand-in home (`HOME`, `CODEX_HOME` or
   `CLAUDE_CONFIG_DIR` pointed at a temp folder). If the user named a folder to use as home, use it
   and never touch the real `~/.claude`, `~/.codex` or `~/.agents`.
2. Ask before widening. Anything that lets the agent do more without asking (an allow rule, a
   sandbox or approval change, a skip-permissions mode) needs the user's yes to the exact lines, with
   the risk in one sentence. A request that names one command ("let it run npm test without
   asking") is that yes for a rule matching only that command, nothing wider. Narrowing (a deny
   rule, a block hook) can go ahead once tested.
3. No secrets in config. A token or password belongs in the environment or a password manager;
   config refers to it by name. Never print a value you find.

**End every reply that changes something with this block:**

```
Change: <one line: what now happens differently>
Agent: Claude Code | Codex | both
File: <path> (<user | project, shared | project, local>)   one line per file
Tested: <command and what it showed> | not tested (<why, and how the user can>)
Undo: <the exact edit or command that puts it back>
```

An audit or a refusal ends with its findings instead (step 6).

## 1. Look before you change

Run `python3 <skill>/scripts/inventory.py --project <project>` (add `--home <folder>` when the user
gave a stand-in home). It lists, per agent, the instruction files that load from that folder, the
skills each agent can see, the settings files with their rule and hook counts, and flags problems
(broken links, name clashes, long or overlapping descriptions, broad allow rules, invalid JSON, a
`CLAUDE.md` that doesn't import `AGENTS.md`). It reads only, and never prints a setting's value.

Then read the files the change will touch, and grep the instructions files for the topic
(`grep -rn -i '<topic>'`) so the new line doesn't repeat or contradict one already there. In
settings and config files look at keys, not values: values can hold tokens.

Which agents? Check both config folders and the project (`AGENTS.md`, `.agents/`, `.codex/`,
`CLAUDE.md`, `.claude/`). If the user runs both, or the project is shared with people who might, the
change goes to both. Say which you chose.

## 2. Pick the mechanism

The question is whether the rule must hold every time, or is guidance the agent should weigh.

| The user wants | Mechanism | Read |
| :--- | :--- | :--- |
| Guidance: how to work here, what to check, what people get wrong | A line in the instructions file at the right scope | `references/instructions.md` |
| Something that must never (or always) happen, and a tool call shows it | A permission rule or a guard hook, plus one instructions line saying why | `references/guards.md` |
| A repeatable job done the user's way (a format, a checklist, a workflow) | A skill | `references/skills.md` |
| To know whether a skill or rule works, or a change broke it | Evals with a baseline | `references/evals.md` |
| To know what is installed, what overlaps, what to clean up | The audit in step 6 | |

Prose can't enforce. If the request says "never" or "always" and a script could check it, use a rule
or hook, and say that a line alone would be skipped some of the time. If no tool call shows the
event (for example "never be rude"), a line is the only option; say so.

Hand these on instead (name the skill if it is installed, otherwise say what the job needs):
- A job that runs on a schedule, in a loop, or keeps the agent going until something is true
  (including a Stop hook that drives a loop): the automation skill, or `/loop` and `/schedule`.
- Which model or effort to use for a task: the model-choice skill. Setting a default model once the
  user has chosen is this skill's job.
- Whether a skill pack or tool someone shared is worth adopting: intake. Installing what intake
  recommended is this skill's job.
- Working out what a session taught: retro. Writing a rule retro proposed, once the user approves it,
  is this skill's job.
- A new repo's first `AGENTS.md`: project-start. A multi-session project's own files: long-project.

## 3. Choose the scope

| Scope | Claude Code | Codex |
| :--- | :--- | :--- |
| Me, everywhere | `~/.claude/CLAUDE.md`, `~/.claude/settings.json`, `~/.claude/skills/` | `~/.codex/AGENTS.md`, `~/.codex/config.toml`, `~/.codex/rules/`, `~/.agents/skills/` |
| Everyone in this repo (committed) | `CLAUDE.md`, `.claude/settings.json`, `.claude/skills/` | `AGENTS.md`, `.codex/config.toml`, `.codex/rules/`, `.agents/skills/` |
| Me, in this repo only | `CLAUDE.local.md`, `.claude/settings.local.json` | no separate file: use the user scope or keep it uncommitted |

A rule for both agents in one repo goes in `AGENTS.md`. Recent Claude Code reads `AGENTS.md` only
while no `CLAUDE.md`, `.claude/CLAUDE.md` or `CLAUDE.local.md` exists in the folder or above it;
once one does, it reads only those unless one holds the line `@AGENTS.md`. So never create a
`CLAUDE.md` or `CLAUDE.local.md` beside an `AGENTS.md` without that import line, and where a
`CLAUDE.md` exists without it, add it and keep the file's content (offer to move shared rules into
`AGENTS.md`). The import also covers older Claude Code versions that don't read `AGENTS.md`. A
personal preference never goes in a committed file, and nothing personal (names, home paths,
employers) goes in a file others will read.

Paths and keys change between versions. If the agent's version is newer than these notes, or a key
is not in `references/`, check the agent's own docs or `--help` before writing it, and say what you
checked.

## 4. Make the smallest change

- Edit only the lines the change needs. Keep the file's style. Never reformat or reorder a config
  file; JSON and TOML edits keep every other key as it was.
- An instructions line states the rule, then the reason in a few words. The reason stops a later
  session deleting a rule it doesn't understand.
- One rule in one place. If the same rule already exists at another scope, say so and change that one
  or remove the duplicate, with the user's OK.
- Before editing a file outside the project, copy it to a scratch folder first, so Undo is a copy back.

## 5. Test it, then show it

Test where it can't hurt (hard rule 1), with the check for the mechanism:

| Change | Test |
| :--- | :--- |
| JSON settings | `python3 -m json.tool <file> > /dev/null`, then the inventory again |
| TOML config | `python3 -c "import tomllib,sys; tomllib.load(open(sys.argv[1],'rb'))" <file>`. Needs Python 3.11+; where `python3` is older (stock macOS), use `uv run --python 3.12 python -c ...` if `uv` is there, or say the syntax was not checked |
| Guard hook | Pipe a sample event into the script, once for a call it must block and once for one it must let through; check the exit code (`references/guards.md`) |
| Codex rule file | `CODEX_HOME=<new empty folder> codex execpolicy check --rules <file> -- <command>` for a blocked and an allowed command |
| Instructions | Re-read the whole file as a new session would: does the new line contradict, repeat or bury another? Then the inventory, to confirm it loads from the project. Optional, where Codex is installed and the user is fine with it contacting OpenAI: `CODEX_HOME=<throwaway copy> codex debug prompt-input` run from the project prints what Codex would load |
| Skill | `references/skills.md` checks, then the evals in `references/evals.md` |

Run every `codex` command, even `--version`, with `CODEX_HOME` set to a new empty folder or a
throwaway copy: Codex writes runtime files into its home folder and may refresh data over the
network.

Only after the test passes, and after the yes for anything that widens access, write to the real file.
If a test can't run here (no Codex installed, a hook event you can't fake), say so in `Tested:` and
give the user the exact command to run.

Tell the user when the change takes effect: Claude Code reloads settings files as they change, but
new skills and instruction files may need a new session; Codex reads rules and config at startup.

## 6. Audit

For "what's installed?", "what should I clean up?", "why didn't my skill load?":

1. Run the inventory (step 1) for the folder the user works in.
2. Read each flagged file. For overlapping descriptions, quote both and say which requests each
   should take. For a skill that didn't load, compare its description with the user's words.
3. Look for what the inventory can't see: plugins and managed settings (ask the agent: `/status` or
   `/plugin` in Claude Code; `codex --help` lists what the installed version offers), and a skill
   installed for one agent that the user also runs in the other.
4. Change nothing. Reply with one row per finding:

```
Audit: <home> / <project>   <n> skills (Claude Code), <n> (Codex)
| Finding | Where | Why it matters | Proposed fix |
Not checked: <what you could not see>
```

Then offer to make the fixes the user picks, one Change block each.

## Limits

- Hooks and rules catch the commands they match; a determined workaround (a script that calls the
  blocked command, an alias, another tool) can get past a pattern. Say so for any block you add.
- These notes were written for the agent versions current in late 2026. Re-check a path or key
  against the agent's docs before relying on it.
