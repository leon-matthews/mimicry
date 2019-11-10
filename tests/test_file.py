
from pathlib import Path
from pprint import pprint as pp
from unittest import TestCase

from mimicry.file import File

from . import DATA_FOLDER


class TestFile(TestCase):
    def test_file_properties(self):
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
        self.assertEqual(
            f.relpath(this_folder),
            Path('data/text1.txt'))
