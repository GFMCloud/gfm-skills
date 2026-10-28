"""Money formatting. Feed totals are strings in pounds, e.g. "12.5" or "1,204.00"."""
from decimal import Decimal, ROUND_HALF_UP


def to_decimal(value):
    if value is None or value == "":
        return Decimal("0")
    return Decimal(str(value).replace(",", ""))


def fmt(value):
    return str(to_decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
