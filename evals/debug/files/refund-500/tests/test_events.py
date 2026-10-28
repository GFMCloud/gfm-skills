import unittest

from payhook.events import to_entry


class EventsTest(unittest.TestCase):
    def test_payment(self):
        e = {"id": "ev_1", "type": "payment.succeeded", "data": {"order": "O-1", "amount": 12.5}}
        self.assertEqual(to_entry(e)["pence"], 1250)

    def test_refund(self):
        e = {"id": "ev_2", "type": "refund.created", "data": {"order": "O-1", "amount": 4.99}}
        self.assertEqual(to_entry(e)["pence"], -499)

    def test_failed_ignored(self):
        e = {"id": "ev_3", "type": "payment.failed", "data": {"order": "O-2"}}
        self.assertIsNone(to_entry(e))
