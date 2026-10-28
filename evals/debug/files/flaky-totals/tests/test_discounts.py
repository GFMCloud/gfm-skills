import unittest
from datetime import datetime

from shop import discounts


class DiscountTest(unittest.TestCase):
    def test_no_code(self):
        self.assertEqual(discounts.apply(10.0), 10.0)

    def test_welcome(self):
        self.assertAlmostEqual(discounts.apply(100.0, "WELCOME5"), 95.0)

    def test_happy_hour_inside(self):
        self.assertAlmostEqual(discounts.apply(100.0, "HAPPYHOUR", datetime(2026, 1, 5, 16, 30)), 85.0)

    def test_happy_hour_outside(self):
        self.assertEqual(discounts.apply(100.0, "HAPPYHOUR", datetime(2026, 1, 5, 9, 0)), 100.0)

    def test_unknown(self):
        with self.assertRaises(ValueError):
            discounts.rate_for("FREE")
