import unittest

from exporter.load import normalise


class NormaliseTest(unittest.TestCase):
    def test_keys(self):
        self.assertEqual(normalise({"Order ID": 1, "Created At": 2, " Customer Email ": 3}),
                         {"order_id": 1, "created_at": 2, "customer_email": 3})
