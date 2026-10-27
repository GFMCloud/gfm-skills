#!/bin/sh
# Build (DEMO). Output goes to public/.
set -eu
cd "$(dirname "$0")"
rm -rf public
mkdir public
cp src/* public/
cp VERSION public/version.txt
echo "Built $(cat VERSION) into public/"
