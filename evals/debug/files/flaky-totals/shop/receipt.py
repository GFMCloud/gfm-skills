"""Plain-text receipts."""
from . import tax


def render(cart, now=None):
    out = []
    for sku, price, qty in cart.lines():
        out.append(f"{sku:<8} {qty:>3} x {price:>6.2f}")
    total = cart.total(now)
    out.append(f"{'TOTAL':<8} {total:>16.2f}")
    out.append(f"{'incl. tax':<10} {tax.tax_included(total):>14.2f}")
    return "\n".join(out)


def save(cart, path, now=None):
    with open(path, "w") as f:
        f.write(render(cart, now) + "\n")
