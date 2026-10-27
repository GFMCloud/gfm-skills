"""Tests for invoice.py. DEMO MATERIAL for a skill trial. Run: python3 -m unittest -q"""
import unittest

from invoice import invoice_total


class InvoiceTotals(unittest.TestCase):
    def test_single_line(self):
        self.assertEqual(invoice_total([(10.00, 1)]), 12.00)

    def test_rounds_to_nearest_penny(self):
        # 7 x 0.99 = 6.93, plus VAT = 8.316
        self.assertEqual(invoice_total([(0.99, 7)]), 8.32)

    def test_bulk_discount_starts_at_ten(self):
        # 10 x 1.00 with 5% off = 9.50, plus VAT = 11.40
        self.assertEqual(invoice_total([(1.00, 10)]), 11.40)

    def test_accounts_rounding_rule(self):
        # Accounts asked for VAT totals to be rounded down to the penny.
        self.assertEqual(invoice_total([(0.99, 7)]), 8.31)


if __name__ == "__main__":
    unittest.main()
