
from unittest import TestCase

from mimicry.cache import Tree
from mimicry.exceptions import NotAFolder

from . import DATA_FOLDER

print(DATA_FOLDER)

class TreeTest(TestCase):
    def test_bad_root(self):
        message = "Given root not a folder: '/banana/apple/sausage'"
        with self.assertRaisesRegex(NotAFolder, message):
            Tree('/banana/apple/sausage')

    def test_read(self):
        t = Tree(DATA_FOLDER)
        t.read()

    def test_read(self):
        t = Tree('~')
        t.read()
