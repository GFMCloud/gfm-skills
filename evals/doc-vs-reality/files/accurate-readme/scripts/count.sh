#!/bin/sh
for f in "$1"/*.md; do printf "%s %s\n" "$(wc -w < "$f")" "$f"; done
