#!/bin/sh
# Builds the git state the diff-vs-plan case needs, inside a trial workspace only.
# Usage: sh evals/planning/prepare.sh <case-id> <workspace>
set -eu
case_id=$1
ws=$2
[ -d "$ws" ] || { echo "no such workspace: $ws" >&2; exit 1; }

case "$case_id" in
  diff-vs-plan)
    git -C "$ws" init -q -b main
    git -C "$ws" config user.name "Demo Fixture"
    git -C "$ws" config user.email "demo@example.com"
    git -C "$ws" config core.hooksPath /dev/null
    git -C "$ws" add PLAN.md invoice.py test_invoice.py
    git -C "$ws" commit -q -m "Before the CSV export (demo fixture)"
    mv "$ws/after/invoice.py" "$ws/invoice.py"
    rmdir "$ws/after"
    ;;
  *)
    echo "no preparation for case: $case_id" >&2
    exit 1
    ;;
esac
git -C "$ws" status --short
