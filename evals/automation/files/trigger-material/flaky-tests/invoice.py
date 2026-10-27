"""Invoice totals for the bakery's wholesale orders. DEMO MATERIAL for a skill trial."""

VAT_RATE = 0.20
BULK_QTY = 10          # 5% off a line of 10 or more
BULK_DISCOUNT = 0.05


def line_total(price, qty):
    total = price * qty
    if qty > BULK_QTY:
        total = total * (1 - BULK_DISCOUNT)
    return total


def invoice_total(lines, vat_rate=VAT_RATE):
    """lines: list of (unit_price, qty). Returns the total with VAT, in pounds, to the penny."""
    subtotal = sum(line_total(price, qty) for price, qty in lines)
    return int(subtotal * (1 + vat_rate) * 100) / 100
