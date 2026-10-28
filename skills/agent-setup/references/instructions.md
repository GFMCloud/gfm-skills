# Instructions files

Read on 2026-10-26 from [Codex AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md)
and the Claude Code [settings](https://code.claude.com/docs/en/settings) and
[memory](https://code.claude.com/docs/en/memory) docs.

## What each agent reads

**Codex:** one global file, `~/.codex/AGENTS.override.md` if it exists, else `~/.codex/AGENTS.md`
(`CODEX_HOME` moves the folder). Then, in each folder from the repo root down to the working folder,
one file: `AGENTS.override.md` if present, else `AGENTS.md`. They are joined root first, so the file
nearest the working folder comes last and wins on conflict. Empty files are skipped. Codex stops
adding files once they reach `project_doc_max_bytes` (default 32 KiB).

**Claude Code:** `~/.claude/CLAUDE.md` and `~/.claude/rules/*.md`, then `CLAUDE.md` (or
`.claude/CLAUDE.md`) in the project and its parent folders, `CLAUDE.local.md` (personal, not
committed) and `.claude/rules/*.md`. A line `@path/to/file.md` imports that file.
Since v2.1.277 it also reads `AGENTS.md` (and `.claude/AGENTS.md`) in the folder and above, but
only while no `CLAUDE.md`, `.claude/CLAUDE.md` or `CLAUDE.local.md` exists there; once one does, it
reads those instead. The user-level `~/.claude/CLAUDE.md` and rules files don't count for that
check. A user setting can make it read both (`claude-md-and-agents-md` in the memory docs).

**For both:** rules in `AGENTS.md`, and a `CLAUDE.md` holding `@AGENTS.md` on its own line.
Claude-only notes can go below the import. Never add a `CLAUDE.md` or `CLAUDE.local.md` to a repo
that relies on `AGENTS.md` without the import line: Claude Code would stop reading `AGENTS.md`.

## What belongs

- What a new session would get wrong: the check command and what passing looks like, the thing
  that must never happen and why, where generated files come from, who owns what.
- Each rule as a rule, then the reason: "Run `make check` before saying a change is done; CI runs the
  same target and a red build blocks the release."
- The commands a rule names, exactly as typed, with paths relative to the repo.

## What doesn't

- What the code or README already says, style the formatter enforces, long background.
- A "never" that a rule or hook could enforce, on its own (add the mechanism; keep one line for why).
- Secrets, tokens, internal hostnames. In a file others read: personal details, home-folder paths,
  employer or client names.
- A personal preference in a committed file (it goes in the user scope or `CLAUDE.local.md`).

For how to word a line, and how to find lines that change nothing, read `writing.md`.

## Before adding a line

1. Grep every file that loads for the topic. If a rule exists, change it rather than adding another.
2. If two files disagree (user says one thing, project another), don't pick silently: tell the user
   which file wins for each agent (nearest file for Codex, project over user for Claude Code) and ask
   which rule they mean.
3. Keep the file short. A long file buries rules; past the Codex byte limit, later files are dropped.
4. After the edit, read the whole file top to bottom as a new session would.

## Override files

`AGENTS.override.md` replaces `AGENTS.md` in its folder for Codex (temporary changes without
touching the shared file). Claude Code ignores it. If you find one, say that Codex is not reading
the `AGENTS.md` beside it.
