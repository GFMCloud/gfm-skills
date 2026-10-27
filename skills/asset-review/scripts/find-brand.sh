#!/bin/sh
# Prints "<source> <folder>" for the first brand source that holds tokens.json or tokens.css:
# project (nearest .agents/brand/ up to the repo root), local (this skill's local/),
# user (~/.agents/brand/), or default (this skill's references/).
# Master copy: tools/find-brand.sh. Brand-aware skills carry an identical copy in scripts/.
skill=$(cd "$(dirname "$0")/.." && pwd)
has() { [ -f "$1/tokens.json" ] || [ -f "$1/tokens.css" ]; }
root=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
d=$(pwd)
while :; do
  if has "$d/.agents/brand"; then echo "project $d/.agents/brand"; exit 0; fi
  if [ "$d" = "$root" ] || [ "$d" = "/" ]; then break; fi
  d=$(dirname "$d")
done
if has "$skill/local"; then echo "local $skill/local"; exit 0; fi
if has "$HOME/.agents/brand"; then echo "user $HOME/.agents/brand"; exit 0; fi
echo "default $skill/references"
