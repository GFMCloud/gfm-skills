"""Feed row -> export row."""
from . import dates, money


def to_export(row):
    return {
        "order_ref": row.get("Order ID", ""),
        "created": dates.day(row.get("Created At")),
        "email": (row.get("Customer Email") or "").lower(),
        "total": money.fmt(row.get("Total")),
    }
