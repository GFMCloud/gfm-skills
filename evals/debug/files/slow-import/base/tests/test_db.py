import unittest

from importer import db


class DbTest(unittest.TestCase):
    def test_insert(self):
        conn = db.connect(":memory:")
        db.insert(conn, {"email": "a@example.com", "name": "A", "town": "X", "joined": "2026-01-01"})
        self.assertEqual(conn.execute("SELECT count(*) FROM customers").fetchone()[0], 1)
