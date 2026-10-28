import json
import os
import tempfile
import unittest

from payhook import app, signing

KEY = "test-secret-for-unit-tests"


class AppTest(unittest.TestCase):
    def setUp(self):
        os.environ["PAYHOOK_SECRET"] = KEY
        self.dir = tempfile.TemporaryDirectory()
        self.ledger = os.path.join(self.dir.name, "ledger.jsonl")

    def tearDown(self):
        self.dir.cleanup()

    def post(self, event, sig=None):
        body = json.dumps(event).encode()
        return app.handle(body, {"X-Signature": sig or signing.sign(body)}, self.ledger)

    def test_payment_recorded(self):
        ev = {"id": "ev_1", "type": "payment.succeeded", "data": {"order": "O-1", "amount": 10}}
        self.assertEqual(self.post(ev), (200, "ok"))

    def test_bad_signature(self):
        ev = {"id": "ev_1", "type": "payment.succeeded", "data": {"order": "O-1", "amount": 10}}
        self.assertEqual(self.post(ev, sig="0" * 64)[0], 401)

    def test_duplicate(self):
        ev = {"id": "ev_9", "type": "payment.succeeded", "data": {"order": "O-9", "amount": 1}}
        self.post(ev)
        self.assertEqual(self.post(ev), (200, "duplicate"))
