"""Date helpers for feed timestamps like 2026-10-25T14:03:00Z."""
from datetime import date, datetime


def parse_ts(value):
    if not value:
        return None
    return datetime.strptime(value[:19], "%Y-%m-%dT%H:%M:%S")


def on_or_after(ts_value, since):
    ts = parse_ts(ts_value)
    return ts is not None and ts.date() >= since


def day(ts_value):
    ts = parse_ts(ts_value)
    return ts.date().isoformat() if ts else ""


__all__ = ["date", "parse_ts", "on_or_after", "day"]
