"""Feed row -> export row. Rows arrive with normalised keys (see load.normalise)."""
from . import dates, money


def to_export(row):
    return {
        "order_ref": row.get("order_id", ""),
        "created": dates.day(row.get("created_at")),
        "email": (row.get("customer_email") or "").lower(),
        "total": money.fmt(row.get("total")),
    }
