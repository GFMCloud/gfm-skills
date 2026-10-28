"""A shopping cart. Lines are (sku, unit_price, qty) tuples."""
from . import discounts, pricing


class Cart:
    def __init__(self, code=None):
        self._lines = []
        self.code = code

    def add(self, sku, qty=1):
        if qty < 1:
            raise ValueError("qty must be at least 1")
        self._lines.append((sku, pricing.price_of(sku), qty))

    def remove(self, sku):
        self._lines = [line for line in self._lines if line[0] != sku]

    def lines(self):
        return list(self._lines)

    def subtotal(self):
        # The scanner sometimes sends the same line twice; count each line once.
        unique = set(self._lines)
        return sum(price * qty for _, price, qty in unique)

    def total(self, now=None):
        return discounts.apply(self.subtotal(), self.code, now)
