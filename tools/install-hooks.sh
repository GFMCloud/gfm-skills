#!/bin/sh
# Turn on this repo's git hooks (.githooks/): checks before every commit and push.
set -e
root=$(cd "$(dirname "$0")/.." && pwd)
chmod +x "$root/.githooks/pre-commit" "$root/.githooks/pre-push"
git -C "$root" config core.hooksPath .githooks
echo "hooks enabled: core.hooksPath = $(git -C "$root" config core.hooksPath)"
deny="${GFM_SKILLS_DENY_FILE:-$HOME/.config/gfm-skills/deny.txt}"
if [ -s "$deny" ]; then echo "employer-terms file: $deny"; else echo "no employer-terms file yet at $deny; pushes stay blocked until it exists"; fi
