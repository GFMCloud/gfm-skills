import os
import tempfile
import unittest
from datetime import datetime

from shop import receipt
from shop.cart import Cart


class ReceiptTest(unittest.TestCase):
    def test_render_has_total(self):
        c = Cart()
        c.add("CUP-07", 2)
        text = receipt.render(c, datetime(2026, 1, 5, 9, 0))
        self.assertIn("TOTAL", text)
        self.assertIn("2.50", text)

    def test_save(self):
        c = Cart("STAFF10")
        c.add("BAG-06")
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "r.txt")
            receipt.save(c, path, datetime(2026, 1, 5, 9, 0))
            with open(path) as f:
                self.assertIn("3.15", f.read())
