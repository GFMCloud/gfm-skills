import unittest

from exporter.money import fmt


class MoneyTest(unittest.TestCase):
    def test_commas(self):
        self.assertEqual(fmt("1,204.5"), "1204.50")

    def test_blank(self):
        self.assertEqual(fmt(""), "0.00")

    def test_half_up(self):
        self.assertEqual(fmt("2.005"), "2.01")
