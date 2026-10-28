"""DEMO fixture for the planning skill evals: invoice totals for a made-up shop."""

import csv

VAT_RATE = 0.20

# Discount codes give a percentage off.
DISCOUNT_CODES = {"WELCOME10": 10, "STAFF25": 25}


def subtotal(lines):
    """lines: list of (unit_price, quantity)."""
    return round(sum(price * qty for price, qty in lines), 2)


def total(lines, code=None):
    amount = subtotal(lines)
    if code:
        amount = amount * (1 - DISCOUNT_CODES[code] / 100)
    return round(amount * (1 + VAT_RATE), 2)


def export_csv(invoices, path):
    """invoices: list of dicts with number, date, lines and an optional code."""
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["number", "date", "subtotal", "total"])
        for inv in invoices:
            code = inv.get("code")
            writer.writerow([inv["number"], inv["date"], subtotal(inv["lines"]), total(inv["lines"], code)])


if __name__ == "__main__":
    import sys
    code = sys.argv[1] if len(sys.argv) > 1 else None
    print(total([(12.50, 2), (4.00, 3)], code))
