"""Turns a provider event into a ledger entry. Amounts are stored in pence."""


def _pence(amount):
    return round(amount * 100)


def to_entry(event):
    kind = event["type"]
    data = event["data"]
    if kind == "payment.succeeded":
        return {"id": event["id"], "order": data["order"], "pence": _pence(data["amount"])}
    if kind == "refund.created":
        return {"id": event["id"], "order": data["order"], "pence": -_pence(data["amount"])}
    if kind == "payment.failed":
        return None
    raise ValueError(f"unknown event type {kind}")
