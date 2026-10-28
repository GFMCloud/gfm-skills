import unittest

from importer import db


class DbTest(unittest.TestCase):
    def test_insert(self):
        conn = db.connect(":memory:")
        db.insert(conn, {"email": "a@example.com", "name": "A", "town": "X", "joined": "2026-01-01"})
        self.assertEqual(conn.execute("SELECT count(*) FROM customers").fetchone()[0], 1)

    def test_exists_ignores_case(self):
        conn = db.connect(":memory:")
        db.insert(conn, {"email": "Bo@Example.com", "name": "B", "town": "", "joined": ""})
        self.assertTrue(db.exists(conn, "bo@example.com"))
        self.assertFalse(db.exists(conn, "cy@example.com"))
