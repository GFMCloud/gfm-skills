#!/bin/sh
# DEMO fixture. Deletes all but the newest $KEEP_COUNT backups in $BACKUP_DIR.
# Backups are named site-YYYY-MM-DD.tar.gz, so name order is date order.
set -eu
cd "$(dirname "$0")"
. ./config.env
total=$(ls "$BACKUP_DIR"/site-*.tar.gz | wc -l)
excess=$((total - KEEP_COUNT))
if [ "$excess" -gt 0 ]; then
  ls "$BACKUP_DIR"/site-*.tar.gz | sort | head -n "$excess" | while read -r f; do
    rm -f "$f"
    echo "deleted $f"
  done
fi
echo "kept $(ls "$BACKUP_DIR"/site-*.tar.gz | wc -l) backups"
