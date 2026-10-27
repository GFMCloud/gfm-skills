"""DEMO fixture for the planning skill evals: invoice totals for a made-up shop."""

VAT_RATE = 0.20

# Discount codes give a percentage off.
DISCOUNT_CODES = {"WELCOME10": 10, "STAFF25": 25}


def subtotal(lines):
    """lines: list of (unit_price, quantity)."""
    return round(sum(price * qty for price, qty in lines), 2)


def total(lines, code=None):
    amount = subtotal(lines)
    if code:
        amount = amount - DISCOUNT_CODES[code]
    return round(amount * (1 + VAT_RATE), 2)


if __name__ == "__main__":
    import sys
    code = sys.argv[1] if len(sys.argv) > 1 else None
    print(total([(12.50, 2), (4.00, 3)], code))
