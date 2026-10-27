#!/bin/sh
# Adds the demo secrets and git history some cases need, inside a trial workspace only.
# The fake values are built here at run time so no secret-shaped string is stored in this repo.
# Usage: sh evals/project-start/prepare.sh <case-id> <workspace>
set -eu
case_id=$1
ws=$2
[ -d "$ws" ] || { echo "no such workspace: $ws" >&2; exit 1; }
fake_key_id="AKIA$(printf 'DEMO%.0s' 1 2 3 4)"
fake_token="ghp_$(printf 'Demo0Token%.0s' 1 2 3 4)"
case "$case_id" in
  folder-with-secrets)
    f="$ws/bakery-site/deploy/upload.js"
    sed "s/__DEMO_KEY_ID__/$fake_key_id/" "$f" > "$f.tmp" && mv "$f.tmp" "$f"
    printf '# Demo values for a skill trial, not real.\nSMTP_USER=orders\nSMTP_PASSWORD=demo-only\n' > "$ws/bakery-site/.env"
    mkdir -p "$ws/bakery-site/node_modules/left-pad"
    printf 'module.exports = (s, n) => String(s).padStart(n);\n' > "$ws/bakery-site/node_modules/left-pad/index.js"
    ;;
  local-repo-to-github)
    r="$ws/notes-app"
    mkdir -p "$r"
    git -C "$r" init -q -b main
    git -C "$r" config user.name "Demo User"
    git -C "$r" config user.email "demo@example.com"
    git -C "$r" config core.hooksPath /dev/null
    printf '# Notes app (demo material for a skill trial)\n\nA tiny notes app. Run: python3 notes.py\n' > "$r/README.md"
    printf 'import sys\nprint("notes:", sys.argv[1:])\n' > "$r/notes.py"
    printf '__pycache__/\n.env\n' > "$r/.gitignore"
    git -C "$r" add -A && git -C "$r" commit -q -m "First version of the notes app"
    printf 'SYNC_TOKEN = "%s"\n' "$fake_token" > "$r/sync.py"
    git -C "$r" add -A && git -C "$r" commit -q -m "Add sync to the backup gist"
    printf 'import os\nSYNC_TOKEN = os.environ["SYNC_TOKEN"]\n' > "$r/sync.py"
    git -C "$r" add -A && git -C "$r" commit -q -m "Read the sync token from the environment"
    git -C "$r" config --unset core.hooksPath
    ;;
  trigger-existing-repo|trigger-uncommitted)
    r="$ws/price-check"
    mkdir -p "$r"
    git -C "$r" init -q -b main
    git -C "$r" config user.name "Demo User"
    git -C "$r" config user.email "demo@example.com"
    git -C "$r" remote add origin https://example.com/demo/price-check.git
    printf '# price-check (demo material for a skill trial)\n\nCompares shop prices. Run: python3 check.py\n' > "$r/README.md"
    printf 'def cheapest(prices):\n    return min(prices, key=prices.get)\n' > "$r/check.py"
    printf '__pycache__/\n.env\n' > "$r/.gitignore"
    git -C "$r" -c core.hooksPath=/dev/null add -A
    git -C "$r" -c core.hooksPath=/dev/null commit -q -m "Compare prices across shops"
    if [ "$case_id" = trigger-uncommitted ]; then
      printf 'def cheapest(prices):\n    if not prices:\n        return None\n    return min(prices, key=prices.get)\n' > "$r/check.py"
    fi
    ;;
  *) echo "nothing to prepare for $case_id" ;;
esac
