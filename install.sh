#!/bin/sh
# Link every skill in this library into Claude Code (~/.claude/skills) and Codex (~/.agents/skills).
# Links, not copies: `git pull` updates the skills, and your skills/<name>/local/ folders survive.
#
#   sh install.sh             install for Claude Code and Codex
#   sh install.sh --claude    Claude Code only
#   sh install.sh --codex     Codex only
#   sh install.sh --uninstall remove the links this script made (nothing else)
#
# It never replaces a file or folder it did not create. macOS and Linux only.
set -eu
lib=$(cd "$(dirname "$0")" && pwd)
mode=install; targets="$HOME/.claude/skills $HOME/.agents/skills"
for a in "$@"; do
  case "$a" in
    --claude) targets="$HOME/.claude/skills" ;;
    --codex) targets="$HOME/.agents/skills" ;;
    --uninstall) mode=uninstall ;;
    *) echo "unknown option: $a"; exit 2 ;;
  esac
done
for t in $targets; do
  created=no
  if [ "$mode" = install ] && [ ! -d "$t" ]; then mkdir -p "$t"; created=yes; fi
  for s in "$lib"/skills/*/; do
    [ -f "$s/SKILL.md" ] || continue
    name=$(basename "$s"); link="$t/$name"; src="${s%/}"
    if [ "$mode" = uninstall ]; then
      if [ -L "$link" ] && [ "$(readlink "$link")" = "$src" ]; then rm "$link"; echo "removed  $link"; fi
      continue
    fi
    if [ -L "$link" ] && [ "$(readlink "$link")" = "$src" ]; then echo "ok       $link"
    elif [ -e "$link" ] || [ -L "$link" ]; then echo "SKIPPED  $link (something else is already there)"
    else ln -s "$src" "$link"; echo "linked   $link"
    fi
  done
  if [ "$created" = yes ]; then echo "note: created $t; restart Codex, or run /reload-skills in Claude Code"; fi
done
