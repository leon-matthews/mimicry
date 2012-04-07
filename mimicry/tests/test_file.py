
import tempfile
from unittest import TestCase

from ..file import File


class TestFile(TestCase):
    def test_empty(self):
        f = File()
        self.assertEqual(f.mtime, None)
        self.assertEqual(f.path, None)
        self.assertEqual(f.sha1, None)
        self.assertEqual(f.size, None)
        self.assertEqual(f.updated, None)

    def test_from_file(self):
        with tempfile.NamedTemporaryFile(prefix='test_file') as tmp:
            f = File(tmp.name)
            print(f)
            f.calculate_sha1()
            print(f)
