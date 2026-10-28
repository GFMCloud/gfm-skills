import unittest

from exporter.transform import to_export


class TransformTest(unittest.TestCase):
    def test_fields(self):
        out = to_export({"Order ID": "A-7", "Created At": "2026-10-03T23:59:00Z",
                         "Customer Email": "Ann@Example.com", "Total": "1,204.5"})
        self.assertEqual(out, {"order_ref": "A-7", "created": "2026-10-03",
                               "email": "ann@example.com", "total": "1204.50"})
