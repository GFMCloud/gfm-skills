"""Discount codes. HAPPYHOUR only counts between 16:00 and 18:00 local time."""
from datetime import datetime

CODES = {"WELCOME5": 0.05, "STAFF10": 0.10, "HAPPYHOUR": 0.15}


def rate_for(code, now=None):
    if not code:
        return 0.0
    if code not in CODES:
        raise ValueError(f"unknown code {code}")
    if code == "HAPPYHOUR":
        hour = (now or datetime.now()).hour
        if not 16 <= hour < 18:
            return 0.0
    return CODES[code]


def apply(amount, code=None, now=None):
    return amount * (1 - rate_for(code, now))
