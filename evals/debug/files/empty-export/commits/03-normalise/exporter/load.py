"""Reads the shop feed: one JSON object per line."""
import json
import re


def _key(name):
    """'Created At' -> 'created_at', 'Order ID' -> 'order_id'."""
    return re.sub(r"[^a-z0-9]+", "_", name.strip().lower()).strip("_")


def normalise(record):
    return {_key(k): v for k, v in record.items()}


def read_feed(path):
    rows = []
    with open(path) as f:
        for n, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(normalise(json.loads(line)))
            except json.JSONDecodeError as e:
                raise ValueError(f"{path}:{n}: bad JSON: {e}") from None
    return rows
