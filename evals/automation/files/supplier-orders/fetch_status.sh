#!/usr/bin/env bash
# DEMO MATERIAL for a skill trial. Prints the supplier's order statuses.
# In real life this fetches the supplier's page; here it reads orders-feed.json.
set -euo pipefail
cd "$(dirname "$0")"
python3 - <<'PY'
import json, datetime
feed = json.load(open("orders-feed.json"))
print("checked at", datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"))
for o in feed["orders"]:
    print(o["id"], o["item"], "->", o["status"])
PY
