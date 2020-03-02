
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

    def test_calculate_totals(self):
        tree = Tree(DATA_FOLDER)
        self.assertEqual(tree.total_files, 7)
        self.assertEqual(tree.total_bytes, 1375)

    def test_calculate_totals_hidden(self):
        tree = Tree(DATA_FOLDER, show_hidden=True)
        self.assertEqual(tree.total_files, 8)
        self.assertEqual(tree.total_bytes, 2286)

    def test_iterate(self):
        tree = Tree(DATA_FOLDER)
        files = []
        total_bytes = 0
        for f in tree.files():
            self.assertIsInstance(f, File)
            total_bytes += f.size
            files.append(f)
        self.assertEqual(len(files), 7)
        self.assertEqual(total_bytes, 1375)

    def test_iterate_ignore(self):
        ignore = [
            'ignore.me',
            'shy/ignore.me.too'
        ]
        tree = Tree(DATA_FOLDER, ignore=ignore)
        relpaths = {f.relative_to(DATA_FOLDER) for f in tree.files()}
        self.assertFalse('ignore.me' in relpaths)
        self.assertFalse('show/ignore.me' in relpaths)
        self.assertEqual(tree.total_files, 5)
        self.assertEqual(tree.total_bytes, 1375)

    def test_repr(self):
        tree = Tree(DATA_FOLDER)
        string = repr(tree)
        self.assertTrue(string.startswith("Tree('/"))
        self.assertTrue(string.endswith("/mimicry/tests/data/')"))

    def test_str(self):
        tree = Tree(DATA_FOLDER)
        string = str(tree)
        pp(string)
        self.assertTrue(string.startswith('/'))
        self.assertTrue(string.endswith('mimicry/tests/data/: 7 files, 1,375 bytes'))
