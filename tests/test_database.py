
import binascii
import os.path
from tempfile import TemporaryDirectory
from unittest import TestCase


from mimicry.database import DB, File, NotUnderRoot


class TestDatabase(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.folder = TemporaryDirectory(prefix='mimicry-')
        cls.db = DB(cls.folder.name)

    @classmethod
    def tearDownClass(cls):
        # ~ import subprocess
        # ~ subprocess.run(['sqlite3', cls.db.path, '.dump'])
        cls.folder.cleanup()

    def test_add(self):
        """
        Add file successfully.
        """
        path = self._make_file('something/else/was/here.png', 1069)

        # Before
        f = self.db.get(path)
        self.assertTrue(f is None)

        # Add
        self.db.add(path)

        # After
        f =  self.db.get(path)
        self.assertIsInstance(f, File)
        self.assertEqual(f.name, 'here.png')
        self.assertEqual(f.relpath, 'something/else/was/here.png')
        self.assertEqual(f.bytes, 1069)
        self.assertGreater(f.mtime, 1e9)
        self.assertGreater(f.updated, 1e9)
        self.assertGreater(f.hashed, 1e9)
        self.assertEqual(
            f.sha256,
            'e42558af9bc23f4aad7e40f39eb6f5c4a224f714a511a3177abc6639df2b3129')

    def test_add_same(self):
        """
        Adding the same file multiple times should create but one record.
        """
        # Add one
        path = self._make_file('some/path/here/and/there.txt', 47)
        self.db.add(path)
        count = self.db.count()

        # Add same file again
        self.db.add(path)
        self.db.add(path)
        self.db.add(path)
        count_after = self.db.count()
        self.assertEqual(count, count_after)

    def test_bytes(self):
        bytes_at_start = self.db.bytes()
        self.assertIsInstance(bytes_at_start, int)
        path = self._make_file('whatever/happens/next.opus', 123)
        self.db.add(path)
        increased_by = self.db.bytes() - bytes_at_start
        self.assertEqual(increased_by, 123)

    def test_calculate_hash(self):
        empty_sha256 = 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'
        empty_path = self._make_file('so/much/empty.txt', 0)
        calculated = self.db._calculate_hash(empty_path).hex()
        self.assertEqual(calculated, empty_sha256)

    def test_create_tables(self):
        """
        Tables have been created automatically.
        """
        query = "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"
        names = [row['name'] for row in self.db.connection.execute(query)]
        self.assertEqual(names, ['files', 'folders', 'metadata'])

    def test_file_iteration(self):
        count = 0
        for f in self.db.files():
            count += 1
            self.assertIsInstance(f, File)
            self.assertEqual(len(f.sha256), 64)
        self.assertGreater(count, 0)

    def test_get_not_under_root(self):
        path = '/not/found/here'
        with self.assertRaises(NotUnderRoot):
            self.db.get(path)

    def _make_file(self, relpath, size):
        """
        Make a single file under our temporary folder.

        Returns full path to file.
        """
        # Create parent directory
        dirname, filename = os.path.split(relpath)
        folder = os.path.join(self.folder.name, dirname)
        os.makedirs(folder)

        # Create file
        path = os.path.join(folder, filename)
        with open(path, 'wb') as fp:
            fp.write(b'@'*size)
        return path
