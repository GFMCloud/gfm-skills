import unittest

from shop.cart import Cart


class CartTest(unittest.TestCase):
    def test_add_and_lines(self):
        c = Cart()
        c.add("TEA-01")
        c.add("MUG-02", 2)
        self.assertEqual([l[0] for l in c.lines()], ["TEA-01", "MUG-02"])

    def test_remove(self):
        c = Cart()
        c.add("TEA-01")
        c.add("JAM-03")
        c.remove("TEA-01")
        self.assertEqual([l[0] for l in c.lines()], ["JAM-03"])

    def test_bad_qty(self):
        with self.assertRaises(ValueError):
            Cart().add("TEA-01", 0)

    def test_unknown_sku(self):
        with self.assertRaises(KeyError):
            Cart().add("NOPE-99")

    def test_double_scan_counted_once(self):
        c = Cart()
        c.add("BAG-06")
        c.add("BAG-06")
        self.assertEqual(c.subtotal(), 3.5)
