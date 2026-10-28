"""The webhook request path: handle(raw_body, headers, ledger_path) -> (status, body)."""
import json

from . import events, ledger, signing


def handle(raw_body, headers, ledger_path="ledger.jsonl"):
    if not signing.valid(raw_body, headers.get("X-Signature")):
        return 401, "bad signature"
    try:
        event = json.loads(raw_body)
    except ValueError:
        return 400, "bad json"
    if ledger.seen(ledger_path, event["id"]):
        return 200, "duplicate"
    entry = events.to_entry(event)
    if entry is not None:
        ledger.append(ledger_path, entry)
    return 200, "ok"
