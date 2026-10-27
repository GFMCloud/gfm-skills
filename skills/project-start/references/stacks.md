# Stacks: what each kind of project starts with

Pick the closest one from what the user said and what is in the folder. Write only what the stack
needs for its first check to run; no empty folders "for later". Each section gives the extra
`.gitignore` lines, the starting files, the check command for `AGENTS.md`, and the rules worth
writing down because people break them early.

## Python (script, command-line tool, pipeline)

- Ignore: `__pycache__/`, `.venv/`, `.pytest_cache/`, `.ruff_cache/`, `*.egg-info/`, `dist/`,
  `build/`, `data/` when the data can be fetched again.
- Files: `pyproject.toml` (name, `requires-python`), one package folder named after the project
  with underscores, `tests/` with one test that runs. With `uv`, run
  `uv init --package --vcs none --no-readme` (plus `--no-pin-python` unless a pin was asked for),
  then check what it wrote.
- Check: `uv run pytest` (or `python3 -m pytest`), plus the linter if one was chosen.
- Rules: pin exact versions in the lock file; anything that calls an outside service gets a
  read-only `--check` mode; never loosen a failing assertion to make a run pass; never commit
  downloaded data or exports.

## Node or TypeScript (web app, tool, library)

- Ignore: `node_modules/`, `dist/`, `build/`, `.next/`, `coverage/`, `*.log`.
- Files: `package.json` with `name`, `private: true` unless it is published, a `test` script that
  runs, and the lock file of the one package manager chosen.
- Check: `npm test` (or the chosen manager's equivalent) and the build command.
- Rules: one package manager and its lock file committed; never hand-edit generated output.

## Static site (hand-written or generated)

- Ignore: the raw exports the site is built from; the build cache.
- Files: `index.html` or the generator's source folder, and the build command written down.
- Check: build it, open it, look at it at phone width; no console errors.
- Rules: if the output is generated, edit the templates, never the output, and name which files
  are generated in `AGENTS.md`. GitHub Pages: on a free plan the repo must be public, and say which
  branch or workflow publishes it.

## Infrastructure as code (Terraform, OpenTofu)

- Ignore: `.terraform/`, `*.tfstate`, `*.tfstate.backup`, `*.tfvars` (keep `*.tfvars.example`),
  `crash.log`, `.terraform.lock.hcl` only if the team chose not to commit it.
- Files: `main.tf`, `versions.tf` (pinned provider and tool versions), `README.md` naming each
  environment.
- Check: `terraform fmt -check`, `terraform validate`, `terraform plan` with no changes expected.
- Rules: state lives in a remote backend, never in git; always plan and read the plan before
  apply; anything that spends money or touches access rights gets a written plan first.

## Self-hosted service (Docker Compose, a home server)

- Ignore: `.env`, volume and data folders, backups.
- Files: `compose.yaml` with pinned image tags (not `latest`), `.env.example` listing variable
  names only, and a `README.md` saying which machine it runs on.
- Check: `docker compose config` parses; the service answers its health check after `up`.
- Rules: back up the data before any upgrade, and test a restore once; pin image tags.

## Writing, notes or data analysis (no app)

- Ignore: exports, caches and notebook checkpoints (`.ipynb_checkpoints/`).
- Files: `README.md` saying what the folder is for and where the source material came from.
- Check: whatever "done" means for the work, written as a command or a checklist.
- Rules: keep raw inputs read only and write results to a separate folder; note the date on any
  number that will go stale.

## Anything else

Use the base `.gitignore`, a `README.md` and `AGENTS.md`, and write the check as `TBD` with what
would settle it. Don't invent a layout.
