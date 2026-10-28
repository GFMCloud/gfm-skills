"""DEMO FIXTURE"""


def clean(rows):
    return [r for r in rows if r.get("status") != "cancelled"]


def total(rows):
    return sum(float(r["amount"]) for r in rows)
