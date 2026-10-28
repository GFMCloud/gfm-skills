"""Append-only ledger file, one JSON entry per line. Duplicate event ids are ignored."""
import json
import os


def seen(path, event_id):
    if not os.path.exists(path):
        return False
    with open(path) as f:
        return any(json.loads(line)["id"] == event_id for line in f if line.strip())


def append(path, entry):
    with open(path, "a") as f:
        f.write(json.dumps(entry) + "\n")
