
from pathlib import Path
from pprint import pprint as pp
import re
import sys
from unittest import TestCase

from mimicry.exceptions import NotAFile
from mimicry.file import File

from . import DATA_FOLDER


class TestFile(TestCase):
    def setUp(self):
        self.path = Path(DATA_FOLDER, 'text1.txt')
        self.file = File(self.path)

    def test_file_not_found(self):
        message = '/no/file/to/be/found/here'
        with self.assertRaisesRegex(NotAFile, message):
            File('/no/file/to/be/found/here')

    def test_basic_properties(self):
        # Basics
        self.assertGreater(self.file.mtime, 1_000_000_000)
        self.assertLess(self.file.mtime, 2_000_000_000)
        self.assertEqual(self.file.name, 'text1.txt')
        self.assertEqual(self.file.size, 1337)

    def test_sha256_hash(self):
        # SHA256 hash is byte string
        hashed = self.file.sha256
        self.assertIsInstance(hashed, bytes)
        self.assertEqual(
            self.file.sha256.hex(),
            '425e0dfc40e7f024204c29926e57a9fbca95e8527b22e16d04dcd57a34e39e43')

        # Called again? Do not recalculate.
        hashed2 = self.file.sha256
        self.assertTrue(hashed is hashed2)

    def test_relative_to(self):
        # Calculate relative path
        this_folder = Path(__file__).parent
        self.assertEqual(self.file.relative_to(this_folder), 'data/text1.txt')

    def test_repr(self):
        r = repr(self.file)
        self.assertTrue(r.startswith("File('/"))
        self.assertTrue(r.endswith("mimicry/tests/data/text1.txt')"))

    def test_str(self):
        self.assertEqual(str(self.file), "text1.txt (1.3kB)")
