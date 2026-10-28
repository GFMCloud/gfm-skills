"""DEMO fixture for the planning skill evals. Run with: python3 -m unittest"""
import unittest

from invoice import subtotal, total


class InvoiceTest(unittest.TestCase):
    def test_subtotal(self):
        self.assertEqual(subtotal([(12.50, 2), (4.00, 3)]), 37.00)

    def test_total_without_code(self):
        self.assertEqual(total([(12.50, 2), (4.00, 3)]), 44.40)


if __name__ == "__main__":
    unittest.main()
