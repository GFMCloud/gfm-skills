#!/bin/sh
# Adds what plain files can't hold (a broken link, git history) inside a trial workspace only.
# Usage: sh evals/agent-setup/prepare.sh <case-id> <workspace>
set -eu
case_id=$1
ws=$2
[ -d "$ws" ] || { echo "no such workspace: $ws" >&2; exit 1; }
demo_git() {
  r=$1
  git -C "$r" init -q -b main
  git -C "$r" config user.name "Demo User"
  git -C "$r" config user.email "demo@example.com"
  git -C "$r" -c core.hooksPath=/dev/null add -A
  git -C "$r" -c core.hooksPath=/dev/null commit -q -m "Demo project for a skill trial"
}
case "$case_id" in
  audit|trigger-overlap)
    ln -s ../../old-skills/old-skill "$ws/home/.claude/skills/old-skill"
    ;;
  rule-both)
    demo_git "$ws/shop-api"
    ;;
  local-note)
    demo_git "$ws/garden-bot"
    ;;
  trigger-commit-rule)
    demo_git "$ws/kiln-log"
    ;;
  *) echo "nothing to prepare for $case_id" ;;
esac
