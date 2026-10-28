import unittest
from datetime import date

from exporter.filters import keep

SINCE = date(2026, 9, 1)


def row(**kw):
    base = {"Order ID": "A-1", "Status": "paid", "Created At": "2026-10-02T10:00:00Z"}
    base.update(kw)
    return base


class FilterTest(unittest.TestCase):
    def test_paid_kept(self):
        self.assertTrue(keep(row(), {"paid", "shipped"}, SINCE))

    def test_cancelled_dropped(self):
        self.assertFalse(keep(row(Status="cancelled"), {"paid", "shipped"}, SINCE))

    def test_old_dropped(self):
        self.assertFalse(keep(row(**{"Created At": "2026-08-30T10:00:00Z"}), {"paid"}, SINCE))

    def test_test_orders_dropped(self):
        self.assertFalse(keep(row(**{"Test Order": True}), {"paid"}, SINCE))
