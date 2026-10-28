# Making or fixing a skill

A skill is a folder with a `SKILL.md`: YAML frontmatter, then Markdown. Claude Code and Codex read
the same format ([Agent Skills spec](https://agentskills.io/specification), read 2026-10-25), so one
folder serves both.

## Before writing

1. Run the inventory. If an installed skill already covers the job (its description overlaps), the
   answer is usually to fix that one, not add a second that competes with it. Say which and ask. If
   the user said not to ask, improve the existing skill (keep a copy of the original for Undo), or
   narrow both descriptions so each names the other in its "Not for" line. Never leave two skills
   competing for the same requests.
2. Write the evals first (`evals.md`): three requests that should load the skill, three near-misses
   that use the same words for a different job, and two or three cases with what a good answer must
   do. Run the cases once without the skill. That baseline is what the skill must beat.

## The folder

```
<name>/
  SKILL.md          required
  references/       optional: detail read only when needed, one level deep
  scripts/          optional: standard-library Python or POSIX sh where possible
  assets/           optional: templates the skill copies
```

## Frontmatter

```yaml
---
name: <name>              # lowercase letters, digits, hyphens; max 64; same as the folder
description: <one paragraph, third person>
---
```

Only `name` and `description` are needed by both agents; `license`, `compatibility` and `metadata`
are allowed. Agent-specific extras (Claude Code `allowed-tools`, Codex `agents/openai.yaml`) are
optional; the skill must work without them.

Don't reuse the name of a built-in or an installed skill: a clash hides one of them or shows both.

## The description decides whether it loads

Both agents see only names and descriptions until a skill is chosen. Weaker models load a skill only
when the description has the user's own words for the request. For the wording itself (one phrase
per branch, which synonyms to cut) and for writing the body, read `writing.md`.

- Lead with the requests in the user's words: "Use when asked to ...".
- Say what it does that a plain answer wouldn't.
- End with "Not for ..." naming the neighbouring jobs, so near-misses go elsewhere.
- About 250 characters, at most 300. Skill lists share a budget (Codex lists about 8,000 characters
  of descriptions when it doesn't know the context size, per its docs read 2026-10-25), so long
  descriptions crowd out other skills. The spec's hard limit is 1,024.
- A colon followed by a space inside an unquoted description breaks the YAML. Quote it or reword.

## The body

- The key steps and any required output line in the first screen; agents may keep only the start
  after compaction. Under 500 lines; move detail to `references/`.
- Say plainly that reading and running the skill's own files is part of using it, and refer to them
  relative to the skill folder, never by a path on this machine.
- Name exact output locations. Say what the skill must not do (send, install, delete) as well as
  what it does.
- No dates, prices or model names unless dated and linked; they go stale.

## Where to install

| Scope | Claude Code | Codex |
| :--- | :--- | :--- |
| User | `~/.claude/skills/<name>/` | `~/.agents/skills/<name>/` |
| Project | `.claude/skills/<name>/` | `.agents/skills/<name>/` (any folder from the working folder up to the repo root) |

For both agents keep one copy and link it into the other folder (`ln -s`); both follow links. On a
machine without links (some Windows set-ups) copy it and say the copies must be updated together.
A new skill may only show up in a new session.

## Checks

- Frontmatter parses, `name` matches the folder, description length: the inventory reports all three.
- Every file the body names exists.
- No secrets, no machine paths, no personal or employer names if anyone else will read it.
- Then the evals, with the skill installed somewhere the trial can see it and the user's real setup
  can't be changed by the trial.

## Built-in helpers

If the agent has its own skill-making helper (Claude Code's skill-creator, for example), it can run
the description and benchmark loop for that agent. It doesn't cover the other agent's folders or the
cross-agent checks above, so do those here.
