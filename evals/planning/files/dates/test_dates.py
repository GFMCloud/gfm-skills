"""DEMO fixture for the planning skill evals. Run with: python3 -m unittest"""
import unittest
from datetime import date

from dates import parse_date
from imports import load_orders
from reports import week_range


class DatesTest(unittest.TestCase):
    def test_iso(self):
        self.assertEqual(parse_date("2026-10-26"), date(2026, 10, 26))

    def test_week_range(self):
        self.assertEqual(week_range("2026-10-19", "2026-10-25"), (date(2026, 10, 19), date(2026, 10, 25)))

    def test_load_orders(self):
        orders = load_orders("orders.csv")
        self.assertEqual(orders[0]["day"], date(2026, 10, 24))


if __name__ == "__main__":
    unittest.main()
