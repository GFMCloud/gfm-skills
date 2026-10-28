import unittest

from importer.validate import problem


def rec(**kw):
    base = {"email": "a@example.com", "name": "A", "town": "", "joined": ""}
    base.update(kw)
    return base


class ValidateTest(unittest.TestCase):
    def test_ok(self):
        self.assertIsNone(problem(rec()))

    def test_no_email(self):
        self.assertEqual(problem(rec(email="")), "no email")
