#!/bin/sh
# DEMO release helper for a skill trial. Do not run it on real files.
# Usage: bump-version.sh <old> <new>
sed -i "s/version = \"$1\"/version = \"$2\"/" VERSION.toml
