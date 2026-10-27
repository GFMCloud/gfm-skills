# Default conventions

Used when no conventions file is found (see the lookup in `SKILL.md`). A conventions file of your
own uses the same keys; any key it leaves out falls back to these.

- **location:** the folder the session is working in. A new project gets its own subfolder there.
- **name:** lowercase letters, digits and hyphens, saying what the project is
  (`receipt-renamer`, not `project1`). No stage words (`-v2`, `-final`, `-new`, `-old`) and no
  dates: git keeps the history. The folder name and any GitHub repo name are the same.
- **name prefixes:** none.
- **visibility:** local only until the user asks for GitHub; private when they do, unless they
  say public.
- **github owner:** the signed-in `gh` account (`gh api user --jq .login`), confirmed with the
  user before anything is created.
- **licence:** MIT for a public repo. No licence file for a private or local one (all rights
  reserved by default); say so in the reply.
- **branch:** `main`.
- **secret hook:** yes (`.githooks/pre-commit` plus `tools/secret_scan.py`).
- **instructions file:** `AGENTS.md`, with a one-line `CLAUDE.md` containing `@AGENTS.md`.
- **first commit message:** `Start <name>: <one line on what it is>`.
- **extra ignore lines:** none.
- **extra required files:** none.
