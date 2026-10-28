import unittest
from datetime import datetime

from shop.cart import Cart

MORNING = datetime(2026, 1, 5, 9, 0)


class TotalsTest(unittest.TestCase):
    def test_totals(self):
        c = Cart()
        for sku in ["TEA-01", "MUG-02", "JAM-03", "OAT-04", "HON-05"]:
            c.add(sku)
        self.assertEqual(c.total(MORNING), 27.39)

    def test_totals_with_code(self):
        c = Cart("WELCOME5")
        c.add("BAG-06", 2)
        self.assertAlmostEqual(c.total(MORNING), 6.65)
