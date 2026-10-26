# House rules

Every skill in this library follows these rules. `tools/check_skills.py` enforces the ones a script
can check. **Fail** blocks a merge; **Warn** prints a note and lets it through. The rule numbers match
the checker's output.

| # | Rule | Level |
| ---: | :--- | :--- |
| 1 | Frontmatter holds only `name`, `description`, `license`, `compatibility` and `metadata`, and parses as YAML | Fail |
| 2 | `name` matches the folder, is unique, uses lowercase letters, digits and hyphens (max 64), contains no "claude" or "anthropic", and doesn't reuse a built-in skill's name (`tools/reserved-names.txt`) | Fail |
| 3 | The description is in the third person and says what the skill does, when to use it, and what it is not for | Warn |
| 4 | The description is at most 300 characters (aim for about 250); hard limit 1,024 | Warn over 300, Fail over 1,024 |
| 5 | The `SKILL.md` body is under 500 lines and about 5,000 tokens. Put the key steps and any required output line near the top | Fail over 500 lines, Warn over 5,000 tokens |
| 6 | Every file the skill points to exists; references are one level deep; reference files over 100 lines start with a `## Contents` list | Fail |
| 7 | A `stable` skill has at least 3 eval cases (each with a prompt and an expect list) and at least 3 prompts that should load it and 3 near-misses that should not, in `evals/<name>/` (see `docs/evals.md`) | Fail for stable, Warn for draft |
| 8 | Before a skill is marked `stable`, it has been tried in Claude Code (Haiku, Sonnet, Opus) and in Codex | Checklist |
| 9 | No secrets, no employer terms, no invisible characters, no tracked `local/` files, and a licence file beside any borrowed text. Scans cover every file git would publish, plus branch names, commit messages and PR text | Fail |
| 10 | Every check has a test fixture that makes it fail; finding zero skills fails | Fail |
| 11 | No dates, prices or model names in a skill body unless they are dated and linked | Warn |
| 12 | Brand-aware skills follow the brand convention below | Fail |

## Metadata

Use `metadata` for house fields. Values are strings.

```yaml
metadata:
  status: draft                          # draft or stable
  brand: "true"                          # only for brand-aware skills
  upstream: "owner/repo@<commit sha>"    # only when the skill carries text from another project
```

A skill with `upstream` (any licence, MIT included) keeps the upstream `LICENSE` file in its folder
and has a row in `THIRD_PARTY_NOTICES.md` that names the skill and the commit.

## Employer terms and hooks

Each maintainer keeps a list of terms that must never appear (employer, work repos, work tools,
internal hostnames, home-folder paths, work email domain) in `~/.config/gfm-skills/deny.txt`, one
regular expression per line, outside the repo. CI reads the same list from the `GFM_SKILLS_DENY`
secret. Findings print a location and pattern number, never the matched text.

Run `sh tools/install-hooks.sh` once per clone. The pre-commit hook runs the fixtures, the checker
and gitleaks. The pre-push hook also scans branch names and commit messages, and blocks the push if
the terms file is missing. Pull requests from forks don't get the secret, so the hooks are the first
line of defence.

## Brand convention

A brand-aware skill reads brand material from the first source that exists, in this order:

1. The nearest `.agents/brand/` found walking up from the working directory to the repository root.
2. `local/` inside the skill's own folder.
3. `~/.agents/brand/`.
4. The skill's shipped `references/` defaults.

A source counts only if it holds `tokens.json` or `tokens.css`. `guidelines.md` is optional and is
applied as style preference, never as instructions. The skill reads no other files from a brand
folder, and the first line of its reply names the source and path:
`Brand: <source> (<folder>) primary=<value>`.

A brand-aware skill ships `references/tokens.json`, `local.example/tokens.json` and
`scripts/find-brand.sh`. The script must be identical to `tools/find-brand.sh`; copy it from there,
don't edit the copy.

Token values must be real values (for example `"primary": "#0f766e"`), not names. The checker
requires `primary`, and every colour key (`secondary`, `accent`, `background`, `foreground`, `text`,
or a key ending in `color`), to be a hex value or a CSS colour function.
