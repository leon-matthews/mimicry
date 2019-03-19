
from unittest import TestCase

from mimicry.cache import Tree
from mimicry.exceptions import NotAFolder

from . import DATA_FOLDER


class TreeTest(TestCase):
    def test_bad_root(self):
        message = "Given root not a folder: '/banana/apple/sausage'"
        with self.assertRaisesRegex(NotAFolder, message):
            Tree('/banana/apple/sausage')

    def test_read(self):
        t = Tree(DATA_FOLDER)
        self.assertEqual(t.num_files, 5)
        self.assertEqual(t.num_bytes, 38)

    def test_str(self):
        t = Tree(DATA_FOLDER)
        self.assertEqual(str(t), '5 files, 38 bytes')

    def test_repr(self):
        t = Tree(DATA_FOLDER)
        self.assertEqual(
            repr(t),
            "Tree('/Users/leonov/Projects/leon/mimicry/tests/data')")
