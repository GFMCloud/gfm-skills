---
name: wizard
description: Writes one bash script that walks the user through console steps only they can do (DNS, dashboards, API keys, CI secrets, cutovers), secrets typed hidden into the keychain or 1Password. Use for "I have to click through the console myself" or "guide me through the keys". Not for planning or deploys.
metadata:
  status: draft
  codex-check: "pending: not yet tried in Codex; must pass before stable"
---

# Wizard

Some steps need the user's own hands: a cloud console, the DNS page at a registrar, a third-party
dashboard, creating or rotating a key, a cutover. Don't hand them a numbered list in chat or ask
them to paste a key. Write one script they run in their own terminal: it opens each page, says
exactly what to click, takes each secret with hidden entry straight into the keychain or
1Password, asks before anything that can't be undone, shows how many stages are left, and ends by
printing what it did and what is still left.

**Rules for every wizard. They hold even when the user asks otherwise; say why in one line.**

- **Never start the wizard in any form**: not to test it, not with input from `/dev/null` or a
  pipe, not to see that it refuses, not with an argument. The only commands that touch it are
  `bash -n`, shellcheck and `scripts/check_wizard.py` (step 5). The wizard does refuse to start
  without a terminal, but that guard is a backstop for mistakes, not a test to run.
- **Secrets never pass through you or a file.** Never ask for a secret in chat, and never write one
  to `.env`, a config file, the script or a command line. The script's helpers take it hidden and
  hand it to the keychain or 1Password, and copy it from there to GitHub on standard input. If the
  user pastes a secret into chat anyway, don't repeat it; say it is now in the transcript and the
  wizard can store a fresh one. The helpers take one-line secrets; a multi-line key (a PEM file,
  a service-account JSON) stays a file: the wizard says where to keep it (a file item in the
  password manager) and records that with `left`.
- **Never read secret values from the project.** Read `.env.example` and docs freely. From `.env`,
  `.env.*` (other than examples), key files or credential files, read key names only
  (`grep -o '^[A-Za-z_][A-Za-z0-9_]*=' .env`), never values. `cat` on those files is not allowed.
- **A typed `yes` before anything irreversible**: `confirm_irreversible` with what will happen and
  why it can't be undone. That covers steps the user clicks (switching nameservers, deleting the
  old site, revoking a key) as well as ones the script does (replacing a GitHub secret).
- **End the reply with the one command to run it**, with the script's absolute path.

## 1. Check it is a wizard job

Use it when the next step needs the user at a console, a dashboard or a password prompt, and the
procedure has more than one step or captures a value. Not a wizard:

- Deciding what to change or in what order before anyone agrees: the planning skill. Once the plan
  is agreed, its user-only steps become a wizard.
- Deploying and checking it works where users reach it: the deploy-verify skill. A wizard can be its
  one human-only step (adding a DNS record, say).
- A job that runs on a schedule or a trigger: the automation skill.
- Creating the repository itself: the project-start skill.
- A step you can do yourself with tools you already have and the user's go: do it, don't script it.

## 2. Read the project for every value

Look before asking. Read the README and docs, `.env.example`, framework and deploy config,
`docker-compose*`, package manifests (which SDKs are used), and `.github/workflows/*`: every
`secrets.NAME` and `vars.NAME` there is a value the wizard must produce (except `GITHUB_TOKEN`,
which GitHub supplies). Find the GitHub repository name from `git remote -v` or the docs. Note
which names already exist (key names only, rule above).

Ask the user only for facts no file holds (which account, which 1Password vault, which domain when
several fit), all in one batch, each with your suggested answer. If nothing is open, don't ask:
write the wizard and list your defaults in the reply.

## 3. Lay out the stages

One stage per focused task, in dependency order (the domain is added at the mail provider before
its DNS records exist; a key is stored before it is copied to GitHub). For each value decide:

| Value | Where it goes | Helper |
| :--- | :--- | :--- |
| Secret (key, token, password, signing secret) | macOS keychain, the default | `keychain_store ITEM "what"` |
| Secret, when the user or project uses 1Password (`op://` references, `op run`) | 1Password vault | `op_store ITEM "what" VAULT` |
| Secret CI reads | GitHub Actions secret, copied from the store | `gh_secret NAME OWNER/REPO keychain:ITEM` or `op://VAULT/ITEM/password` |
| Non-secret CI value | GitHub Actions variable | `ask VAR "prompt"`, then `gh_variable NAME OWNER/REPO "$VAR"` |
| Non-secret app setting, or an `op://` reference | the project's config file | `config_set FILE KEY VALUE` |
| An old plain-text secret line to take out | the project's config file | `config_remove FILE KEY` |
| Nothing kept (a switch flipped, a record added) | the summary | `did "what was done"` |

Name keychain and 1Password items after the variable the app reads (`PAYMENTS_SECRET_KEY`), so the
closing summary tells the user how to load each one. When the app reads secrets from `.env`, say in
the reply how it gets them now: with 1Password, `.env` holds `op://` references and the app starts
under `op run --env-file .env -- <command>`; with the keychain, an `export` line that reads
`security find-generic-password -a "$USER" -s ITEM -w` in the shell that starts it.

**Click paths.** Write the path a stranger could follow ("Domains, then Add domain, then copy the
three records"). Take it from the project's docs or the provider's current docs. When you can't
confirm the current screen (no docs, or a fetch is refused, which is final), say what to look for
instead of inventing menu names, and add `note "Screen names may differ: look for <thing>."`. Never
make up a URL: use one from the docs or the provider's home page.

## 4. Write the script

Copy `assets/wizard-template.sh` from this skill's folder to `wizard-<topic>.sh` in the project root
(or the path the user names). Reading and copying the skill's own files is part of using it; the
copy must not mention the skill's folder.

- Leave everything above the `# ===== STAGES` line exactly as it is; the checker compares it with
  the template. Replace every `EXAMPLE` line below it.
- Set `WIZARD_TITLE`, a one-line `WIZARD_ABOUT` (what it does, what to have open), and
  `TOTAL_STAGES` to the number of `stage` calls.
- Inside `main`, per stage: `stage "Title"`, then `open_url` before asking for anything from that
  page, `step` for each click, `pause` while the user does it, then the helper that keeps the value.
  Also available: `say`, `note`, `warn`, `did "what was done"`, `left "what is still to do"`. Every
  `stage` call sits directly in `main`, so the checker can count them.
- `confirm` and `confirm_irreversible` always go inside an `if` (or before `&&`). On their own
  line, a "no" stops the whole script. An irreversible step looks like this:

  ```bash
  if confirm_irreversible "Delete the old site at OldHost" "OldHost keeps no backups."; then
    step "Sites, then crumb-demo, then Delete site."
    pause
    did "deleted the old site at OldHost"
  else
    left "delete the old site at OldHost once the new one is confirmed"
  fi
  ```

- Keep the last line `_wizard_run "$@"`. Never add `set -x`, `read`, direct `security`, `op` or
  `gh secret` calls, or edits to `.env` with `sed` or redirects; the helpers do that work so values
  stay off command lines and out of output. Write for bash 3.2 (the macOS default): no associative
  arrays, `${var,,}` or `mapfile`.
- Make it executable: `chmod +x`. Don't commit it unless the user asks; it holds no secrets, so it
  can be committed when it is a setup path others will rerun.

## 5. Check it, never run it

```bash
bash -n wizard-<topic>.sh
shellcheck wizard-<topic>.sh
python3 <this skill>/scripts/check_wizard.py wizard-<topic>.sh --ci .github/workflows
```

Leave out `--ci` when the project has no workflows. Fix every FAIL and rerun until `RESULT: PASS`;
read each WARN and fix it or say in the reply why it stands. If the checker seems wrong about a
line that follows this skill, say so in the reply rather than bending the script to suit it.

The checker prints a stage map: trace it against step 3 so every value is captured once and lands
where you planned, and every `gh_secret` name matches the workflow exactly. If shellcheck is not
installed, say so; don't install it.

## 6. Reply

1. The bottom line: what the wizard covers and how many stages.
2. A table: stage, what the user does there, value captured, where it lands.
3. What you could not check: click paths you could not confirm, that the store and `gh` work on
   their machine (the first real run is the test), defaults you chose.
4. How the app reads the stored secrets afterwards, if that changed.
5. Last line, the exact command:

```bash
bash /absolute/path/to/wizard-<topic>.sh
```
