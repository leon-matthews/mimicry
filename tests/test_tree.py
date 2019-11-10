
from pprint import pprint as pp
from unittest import TestCase

from mimicry.exceptions import NotAFolder
from mimicry.file import File
from mimicry.tree import Tree

from . import DATA_FOLDER


class TreeTest(TestCase):
    def test_bad_root(self):
        message = "Given root not a folder: '/banana/apple/sausage'"
        with self.assertRaisesRegex(NotAFolder, message):
            Tree('/banana/apple/sausage')

    def test_files(self):
        for f in Tree(DATA_FOLDER).files():
            self.assertIsInstance(f, File)

    def test_read(self):
        t = Tree(DATA_FOLDER)
        self.assertEqual(t.total_files, 5)
        self.assertEqual(t.total_bytes, 1375)

    def test_repr(self):
        t = Tree(DATA_FOLDER)
        string = repr(t)
        self.assertTrue(string.startswith("Tree('/"))
        self.assertTrue(string.endswith("/mimicry/tests/data')"))

    def test_str(self):
        t = Tree(DATA_FOLDER)
        string = str(t)
        self.assertTrue(string.startswith('/'))
        self.assertTrue(string.endswith('mimicry/tests/data/: 5 files, 1,375 bytes'))
