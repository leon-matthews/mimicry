
from pathlib import Path
from pprint import pprint as pp
import re
import sys
from unittest import TestCase

from mimicry.file import File

from . import DATA_FOLDER


class TestFile(TestCase):
    def test_file_not_found(self):
        message = '/no/file/to/be/found/here'
        with self.assertRaisesRegex(FileNotFoundError, message):
            File('/no/file/to/be/found/here')

    def test_properties(self):
        path = Path(DATA_FOLDER, 'text1.txt')
        self.assertTrue(path.is_file())

        f = File(path)
        self.assertEqual(f.size, 1337)
        self.assertGreater(f.mtime, 1_000_000_000)
        self.assertLess(f.mtime, 2_000_000_000)
        self.assertEqual(
            f.sha256.hex(),
            '425e0dfc40e7f024204c29926e57a9fbca95e8527b22e16d04dcd57a34e39e43')
        this_folder = Path(__file__).parent

    def test_repr(self):
        path = Path(DATA_FOLDER, 'text1.txt')
        f = File(path)
        self.assertTrue(re.match(r"^File\(.*tests/data/text1.txt'\)$", repr(f)))

    def test_str(self):
        path = Path(DATA_FOLDER, 'text1.txt')
        f = File(path)
        self.assertEqual(str(f), "text1.txt (1.3kB)")
