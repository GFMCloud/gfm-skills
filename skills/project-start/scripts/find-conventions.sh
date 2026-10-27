#!/bin/sh
# Prints "Conventions: <source> (<file>)" for the first conventions file that exists:
# project (nearest .agents/project-start/conventions.md walking up from START, stopping before the
# home folder or at /), local (this skill's local/conventions.md),
# user (~/.agents/project-start/conventions.md), or default (this skill's references/defaults.md).
# Usage: sh find-conventions.sh [START]   START is where the new project will live (default: here).
skill=$(cd "$(dirname "$0")/.." && pwd)
start=${1:-.}
if [ ! -d "$start" ]; then echo "find-conventions: not a folder: $start" >&2; exit 1; fi
d=$(cd "$start" && pwd)
case "$d" in "$skill"|"$skill"/*)
  echo "find-conventions: run this from the project's folder, not from inside the skill" >&2 ;;
esac
f=.agents/project-start/conventions.md
while [ "$d" != "$HOME" ]; do
  if [ -f "$d/$f" ]; then echo "Conventions: project ($d/$f)"; exit 0; fi
  if [ "$d" = "/" ]; then break; fi
  d=$(dirname "$d")
done
if [ -f "$skill/local/conventions.md" ]; then echo "Conventions: local ($skill/local/conventions.md)"; exit 0; fi
if [ -f "$HOME/$f" ]; then echo "Conventions: user ($HOME/$f)"; exit 0; fi
echo "Conventions: default ($skill/references/defaults.md)"
