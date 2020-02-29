
import os.path
from pathlib import Path
from pprint import pprint as pp
from tempfile import TemporaryDirectory
from unittest import TestCase


from mimicry.database import DB, FileRecord, NotUnderRoot
from mimicry.file import File


class TestCaseData(TestCase):
    """
    `TestCase` that also creates temporary folder and database.

    The folder *and* database persist accross all methods - use with care.
    """
    @classmethod
    def setUpClass(cls):
        cls.folder = TemporaryDirectory(prefix='mimicry-')
        cls.db_path = Path(cls.folder.name) / 'mimicry.db'
        cls.db = DB(cls.db_path)

    @classmethod
    def tearDownClass(cls):
        # ~ import subprocess; subprocess.run(['sqlite3', cls.db_path, '.dump'])
        cls.folder.cleanup()

    def make_file(self, relpath, size):
        """
        Make a file under our temporary folder.

        Returns (`Path`): Path to created file.
        """
        # Create parent directory
        relpath = Path(relpath)
        folder = Path(self.folder.name) / relpath.parent
        folder.mkdir(exist_ok=True, parents=True)

        # Create file
        path = folder / relpath.name
        with open(path, 'wb') as fp:
            fp.write(b'@'*size)
        return Path(path)


class TestAdd(TestCaseData):
    def test_add(self):
        """
        Add file successfully.
        """
        path = self.make_file('something/else/was/here.png', 1069)

        # Before
        record = self.db.get(path)
        self.assertTrue(record is None)

        # Add
        self.db.add(path)

        # After
        record = self.db.get(path)
        self.assertIsInstance(record, FileRecord)
        self.assertEqual(record.name, 'here.png')
        self.assertEqual(record.relpath, 'something/else/was/here.png')
        self.assertEqual(record.size, 1069)
        self.assertGreater(record.mtime, 1e9)
        self.assertEqual(
            record.sha256.hex(),
            'e42558af9bc23f4aad7e40f39eb6f5c4a224f714a511a3177abc6639df2b3129'
        )

    def test_add_same(self):
        """
        Adding the same file multiple times should create just one record.
        """
        # Add one
        path = self.make_file('some/path/here/and/there.txt', 47)
        self.db.add(path)
        count = self.db.files_count()

        # Add same file again
        self.db.add(path)
        self.db.add(path)
        self.db.add(path)
        count_after = self.db.files_count()
        self.assertEqual(count, count_after)


class TestDelete(TestCaseData):
    def test_delete(self):
        # Start with none
        self.assertEqual(self.db.files_count(), 0)
        self.assertEqual(self.db.folders_count(), 0)

        # Create files
        paths = []
        paths.append(self.make_file('soon/be/dead.txt', 512))
        paths.append(self.make_file('gonna/bite/it.txt', 345))
        for path in paths:
            self.db.add(path)
        self.assertEqual(self.db.files_count(), 2)
        self.assertEqual(self.db.folders_count(), 2)

        # Delete all files.
        # Note that folder records are *not* removed.
        for path in paths:
            self.db.delete(path)
        self.assertEqual(self.db.files_count(), 0)
        self.assertEqual(self.db.folders_count(), 2)


class TestQuery(TestCaseData):
    """
    Read only queries over same database.
    """
    def setUp(self):
        # Create two files
        super().setUp()
        self.db.add(self.make_file('some/path/first.webp', 47))
        self.db.add(self.make_file('some/path/second.zst', 48))

    def test_create_tables(self):
        """
        Tables have been created automatically.
        """
        query = "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"
        names = [row['name'] for row in self.db.connection.execute(query)]
        self.assertEqual(names, ['files', 'folders', 'metadata'])

    def test_file_iteration(self):
        count = 0
        for record in self.db.files():
            count += 1
            self.assertIsInstance(record, FileRecord)
            self.assertEqual(len(record.sha256), 32)
            self.assertEqual(len(record.sha256.hex()), 64)
        self.assertGreater(count, 0)
        self.assertEqual(count, self.db.files_count())

    def test_files_size(self):
        bytes_at_start = self.db.files_size()
        self.assertIsInstance(bytes_at_start, int)
        path = self.make_file('whatever/happens/next.opus', 123)
        self.db.add(path)
        increased_by = self.db.files_size() - bytes_at_start
        self.assertEqual(increased_by, 123)

    def test_get_missing(self):
        path = self.db_path.parent / 'missing.png'
        record = self.db.get(path)
        self.assertTrue(record is None)

    def test_get_not_under_root(self):
        path = '/not/found/here'
        with self.assertRaises(NotUnderRoot):
            self.db.get(path)
