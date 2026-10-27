#!/bin/sh
# Deploy the built site (DEMO: the hosts are local folders served by a demo server).
set -eu
cd "$(dirname "$0")"
env="${1:-}"
case "$env" in
  staging|production) ;;
  *) echo "usage: ./deploy.sh staging|production"; exit 1 ;;
esac
rm -rf "hosts/$env"
mkdir -p "hosts/$env"
cp -R dist/. "hosts/$env/"
echo "OK  Deployed to $env"
