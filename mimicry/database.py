
from collections import defaultdict, namedtuple
import hashlib
import logging
from pprint import pprint as pp
import os.path
import sqlite3
import textwrap

from .exceptions import NotUnderRoot


logger = logging.getLogger(__name__)


File = namedtuple('File', 'name path relpath bytes mtime updated sha256 hashed')


class DB:
    """
    Store metadata for a file tree.

    An SQLite database file (`mimicry.db`) is created in the root of the
    given file tree will maintain metadata about that tree, including a hash
    of file contents, about every folder and file found.

    It is an error to try and perform operations outside the file tree's
    root. A `NotUnderRoot` exception will be raised if attempted.
    """
    def __init__(self, root):
        """
        Create or open database file with given path.

        The database file will be created
        """
        self.root = os.path.abspath(root)
        self.path = os.path.join(self.root, 'mimicry.db')
        self.connect(self.path)

    def add(self, path):
        """
        Read single file with given path to the database.
        """
        path = self._clean_path(path)
        cursor = self.connection.cursor()
        cursor.execute('SAVEPOINT add_file;')
        try:
            self._do_add(path, cursor)
            cursor.execute("RELEASE add_file;")
        except sqlite3.Error:
            cursor.execute("ROLLBACK TO add_file;")
            raise

    def connect(self, path):
        self.connection = sqlite3.connect(path, isolation_level=None)
        self.connection.row_factory = sqlite3.Row
        # ~ self.connection.set_trace_callback(print)
        self._check_schema()
        self._run_pragmas()

    def delete(self, path):
        """
        Delete the file record with the given path.
        """
        path = self._clean_path(path)
        data = self._get(path)
        pk = data['id']
        self.connection.execute('DELETE FROM files WHERE id=?;', (pk,))
        self.connection.commit()

    def duplicates(self):
        """
        Iterate over duplicate files.
        """
        duplicates = defaultdict(list)

        query = ("SELECT count(*) AS count, sha256, bytes FROM "
                 "files GROUP BY sha256 HAVING count > 1;")

        query = ("SELECT * FROM files WHERE sha256 IN "
                 "(SELECT sha256 FROM files GROUP BY sha256 HAVING count(*) > 1);")
        for row in self.connection.execute(query):
            f = File(fields=row)
            duplicates[f.sha256].append(f)
        return duplicates

    def files(self):
        """
        Iterate over every file in database.
        """
        query = textwrap.dedent("""
            SELECT name, bytes, mtime, updated, sha256, hashed, relpath
                FROM files INNER JOIN folders ON files.folder = folders.id
        """).strip()
        for row in self.connection.execute(query):
            data = dict(row)
            data['relpath'] = os.path.join(data['relpath'], data['name'])
            data['path'] = os.path.join(self.root, data['relpath'])
            data['sha256'] = data['sha256'].hex()
            yield File(**data)

    def files_count(self):
        """
        Return the total number of file records.
        """
        cursor = self.connection.execute("SELECT count(*) FROM files;")
        return cursor.fetchone()[0]

    def files_size(self):
        """
        Return sum of the bytes accross of all file records.
        """
        cursor = self.connection.execute("SELECT sum(bytes) FROM files;")
        return cursor.fetchone()[0]

    def get(self, path):
        """
        Return a single `File` record.

        Args:
            path (str): Path to file.

        Returns:
            A `File` namedtuple, or `None` if not found.
        """
        data = self._get(path)
        if data is None:
            return None
        data['path'] = path
        data['relpath'] = relpath
        data['sha256'] = data['sha256'].hex()
        return File(**data)

    def _get(self, path):
        """
        Fetch data about a single file, raw.

        Args:
            path (str): Path to file

        Returns:
            Raw dictionary of data from database layer.
        """
        path = self._clean_path(path)
        relpath = os.path.relpath(path, self.root)
        folder, filename = os.path.split(relpath)
        query = textwrap.dedent("""
            SELECT files.id as id, name, bytes, mtime, updated, sha256, hashed
                FROM files INNER JOIN folders ON files.folder = folders.id
                WHERE name=:filename AND
                      folder=(SELECT id FROM folders WHERE relpath=:folder);
        """).strip()
        cursor = self.connection.cursor()
        cursor.execute(query, {'folder':  folder, 'filename': filename})
        row = cursor.fetchone()

        if row is None:
            return None
        data = dict(row)
        return data

    def _calculate_hash(self, path):
        BUFFSIZE = 4096 * 1000
        sha256 = hashlib.sha256()
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(BUFFSIZE), b''):
                sha256.update(chunk)
        return sha256.digest()

    def _check_schema(self):
        """
        Create database structure, if required.

        All times are Unix epoch's.

        Should only be run on an empty database file.
        """
        schema = textwrap.dedent("""

        CREATE TABLE IF NOT EXISTS files (
            -- Metadata every file found under database root
            id              INTEGER PRIMARY KEY,
            name            TEXT NOT NULL,          -- File's name
            bytes           INTEGER,                -- File's size
            mtime           INTEGER,                -- File's mtime
            updated         INTEGER,                -- Time metadata last updated
            sha256          BLOB,                   -- Binary sha256 hash
            hashed          INTEGER,                -- Time hash was last calculated
            folder          INTEGER NOT NULL,       -- Link to parent folder
            FOREIGN KEY(folder) REFERENCES folders(id),
            UNIQUE  (name, folder)
        );

        CREATE TABLE IF NOT EXISTS folders (
            -- Every folder found under database root
            id              INTEGER PRIMARY KEY,
            relpath         TEXT UNIQUE NOT NULL    -- Path relative to database
        );

        CREATE TABLE IF NOT EXISTS metadata (
            -- Single entry table containing DB metadata
            id              INTEGER PRIMARY KEY,
            label           TEXT NOT NULL,          -- User label
            root            TEXT NOT NULL,          -- Full path to last mount point
            device_model    TEXT,                   -- Storage device model
            device_serial   TEXT,                   -- Storage device serial number
            created         INTEGER NOT NULL,       -- Database creation time
            updated         INTEGER NOT NULL,       -- Time of completed update
            CHECK (rowid=1)                         -- Only one row allowed
        );

        """)
        self.connection.executescript(schema)
        self.connection.commit()

    def _clean_path(self, path):
        """
        Clean path, and check for validity.

        Raises `NotUnderRoot` if given path is not... under... root...
        """
        # Check that path is under our root
        path = os.path.abspath(path)
        commonpath = os.path.commonpath([path, self.root])
        if not commonpath.startswith(self.root):
            message = f"Given path not under database's root folder: {path}"
            raise NotUnderRoot(message)
        return path

    def _do_add(self, path, cursor):
        relpath = os.path.relpath(path, self.root)
        folder, filename = os.path.split(relpath)

        cursor.execute("INSERT OR IGNORE INTO folders(relpath) VALUES (?)", (folder,))
        cursor.execute("SELECT id FROM folders WHERE relpath=?;", (folder,))
        folder_id = cursor.fetchone()['id']

        # Build parameters
        parameters = {
            'name': filename,
            'bytes': os.path.getsize(path),
            'mtime': int(os.path.getmtime(path)),
            'folder': folder_id,
            'sha256': self._calculate_hash(path),
        }

        # Create bare file
        query = "INSERT OR IGNORE INTO files (name, folder) VALUES (:name, :folder);"
        cursor.execute(query, parameters)

        # Update file
        # We do this in two steps to preserve the file's rowid. Running a single
        # 'INSERT OR REPLACE' increments that.
        query = textwrap.dedent("""
            UPDATE files SET
                bytes=:bytes, mtime=:mtime, sha256=:sha256,
                hashed=strftime('%s'), updated=strftime('%s')
                WHERE name=:name AND folder=:folder;
        """).strip()
        cursor.execute(query, parameters)

    def _run_pragmas(self):
        """
        Configure database connection.
        """
        cursor = self.connection.cursor()
        self.connection.execute('PRAGMA cache_size = -16384;')    # 16MiB
        cursor.execute("PRAGMA foreign_keys = ON;")
        cursor.execute('PRAGMA journal_mode = WAL;')
        cursor.execute("PRAGMA synchronous = OFF;")
        cursor.execute('PRAGMA temp_store = MEMORY;')
