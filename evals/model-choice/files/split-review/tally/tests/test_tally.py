import os
import tempfile
import unittest

import tally


class TallyTest(unittest.TestCase):
    def test_counts(self):
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as fh:
            fh.write("one two\nthree\n")
        try:
            self.assertEqual(tally.count(fh.name)[:2], (3, 2))
        finally:
            os.unlink(fh.name)


if __name__ == "__main__":
    unittest.main()
