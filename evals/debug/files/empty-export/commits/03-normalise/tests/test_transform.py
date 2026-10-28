import unittest

from exporter.transform import to_export


class TransformTest(unittest.TestCase):
    def test_fields(self):
        out = to_export({"order_id": "A-7", "created_at": "2026-10-03T23:59:00Z",
                         "customer_email": "Ann@Example.com", "total": "1,204.5"})
        self.assertEqual(out, {"order_ref": "A-7", "created": "2026-10-03",
                               "email": "ann@example.com", "total": "1204.50"})
