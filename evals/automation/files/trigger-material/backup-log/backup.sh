#!/usr/bin/env bash
# DEMO MATERIAL for a skill trial. Copies new photos into the backup folder.
cd photos
mkdir -p ../backup
cp -n *.jpg ../backup/
echo "Backup done"
