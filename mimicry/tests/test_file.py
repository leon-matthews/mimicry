
import tempfile
from unittest import TestCase

from ..file import File


class TestFile(TestCase):
    def test_empty(self):
        """
        Fields are initialised properly.
        """
        f = File()
        self.assertEqual(f.mtime, None)
        self.assertEqual(f.path, None)
        self.assertEqual(f.sha1, None)
        self.assertEqual(f.size, None)
        self.assertEqual(f.updated, None)

    def test_empty_file(self):
        """
        Basic operations on an empty file.
        """
        with tempfile.NamedTemporaryFile(prefix='mimicry-') as tmp:
            f = File(tmp.name, read_sha1=False)

            # Regular fields
            self.assertTrue(f.path.startswith('/tmp'))
            self.assertGreater(f.mtime, 1e9)
            self.assertGreater(f.updated, 1e9)
            self.assertEqual(f.size, 0)

            # Native binary sha1
            self.assertEqual(f.format_sha1(), None)
            f.update()
            self.assertEqual(type(f.sha1), bytes)
            self.assertEqual(f.sha1,
                b'\xda9\xa3\xee^kK\r2U\xbf\xef\x95`\x18\x90\xaf\xd8\x07\t')

            # Format to hex
            self.assertEqual(f.format_sha1(),
                'da39a3ee5e6b4b0d3255bfef95601890afd80709')

    def test_update(self):
        """
        Write to file after creation.
        """
        with tempfile.NamedTemporaryFile(prefix='mimicry-') as tmp:
            f = File(tmp.name)
            self.assertEqual(f.format_sha1(),
                'da39a3ee5e6b4b0d3255bfef95601890afd80709')

            with open(tmp.name, 'wt') as fp:
                fp.write('Hello, world\n')

            f.update()
            self.assertEqual(f.format_sha1(),
                '7b4758d4baa20873585b9597c7cb9ace2d690ab8')
