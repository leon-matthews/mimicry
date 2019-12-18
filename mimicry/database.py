
from collections import defaultdict, namedtuple
from dataclasses import dataclass
import hashlib
import logging
import os.path
from pathlib import Path
from pprint import pprint as pp
import sqlite3
import textwrap

from .exceptions import NotUnderRoot
from .file import File


logger = logging.getLogger(__name__)


@dataclass
class FileRecord:
    """
    File metadata from database.
    """
    name: str
    path: str
    size: int
    mtime: int
    sha256: bytes

    @classmethod
    def from_database(cls, root, row):
        """
        Create object from database row data.

        Args:
            root (str): Root folder of database.
            row (dict): Raw row database.
        """
        kwargs = {
            'name': row['name'],
            'path': root / row['relpath'] / row['name'],
            'size': row['size'],
            'mtime': row['mtime'],
            'sha256': row['sha256'],
        }
        return cls(**kwargs)


class DB:
    """
    Store metadata for a file tree.

    An SQLite database file (`mimicry.db`) is created in the root of the
    given file tree will maintain metadata about that tree, including a hash
    of file contents, about every folder and file found.

    It is an error to try and perform operations outside the file tree's
    root. A `NotUnderRoot` exception will be raised if attempted.
    """
    def __init__(self, path):
        """
        Open existing, or create database file.

        Args:
            path (Path): Path to database file
            root (Path): Root directory of tree.
        """
        self.root = path.parent
        if not self.root.is_dir():
            raise RuntimeError(f"Database root must be an existing folder: {self.root}")
        self.connection = self._connect(path, verbose=False)
        self._check_schema()
        self._run_pragmas()

    def _clean_path(self, path):
        """
        TODO: where and when?
        Clean path, and check for validity.

        Raises `NotUnderRoot` if given path is not... under... root...
        """
        # Check that path is under our root
        try:
            commonpath = path.relative_to(self.root)
        except ValueError:
            message = f"Given path not under '{self.root!s}': {path}"
            raise NotUnderRoot(message) from None
        return path

    def add(self, path):
        """
        Add or update single file record in database.

        Args:
            path: Full path to file.
        """
        file_ = File(path)
        cursor = self.connection.cursor()
        cursor.execute('SAVEPOINT add_file;')
        try:
            self._do_add(cursor, file_)
            cursor.execute("RELEASE add_file;")
        except sqlite3.Error:
            cursor.execute("ROLLBACK TO add_file;")
            raise

    def delete(self, path):
        """
        Delete the file record with the given path.
        """
        data = self.get_row(path)
        pk = data['id']
        self.connection.execute('DELETE FROM files WHERE id=?;', (pk,))
        self.connection.commit()

    def duplicates(self):
        """
        Iterate over duplicate files.
        """
        duplicates = defaultdict(list)

        query = ("SELECT count(*) AS count, sha256, size FROM "
                 "files GROUP BY sha256 HAVING count > 1;")

        query = ("SELECT * FROM files WHERE sha256 IN "
                 "(SELECT sha256 FROM files GROUP BY sha256 HAVING count(*) > 1);")
        for row in self.connection.execute(query):
            f = FileRecord(fields=row)
            duplicates[f.sha256].append(f)
        return duplicates

    def files(self):
        """
        Iterate over every file in database.
        """
        query = textwrap.dedent("""
            SELECT name, size, mtime, sha256, updated, relpath
                FROM files INNER JOIN folders ON files.folder = folders.id
        """).strip()
        for row in self.connection.execute(query):
            data = dict(row)
            yield FileRecord.from_database(self.root, data)

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
        cursor = self.connection.execute("SELECT sum(size) FROM files;")
        return cursor.fetchone()[0]

    def folders_count(self):
        cursor = self.connection.execute("SELECT count(*) FROM folders;")
        return cursor.fetchone()[0]


    def get(self, path):
        """
        Return a single `FileRecord` record.

        Args:
            path (Path): Path to file.

        Returns:
            A `File` namedtuple, or `None` if not found.
        """
        row = self.get_row(path)
        if row is None:
            return None
        return FileRecord.from_database(self.root, row)

    def _connect(self, path, verbose=False):
        """
        Connect to database.

        Args:
            path
        """
        connection = sqlite3.connect(path, isolation_level=None)
        connection.row_factory = sqlite3.Row
        if verbose:
            connection.set_trace_callback(logger.debug)
        return connection

    def get_row(self, path):
        """
        Fetch data about a single file, raw.

        Args:
            path (str): Path to file

        Returns:
            Raw dictionary of data from database layer.
        """
        query = textwrap.dedent("""
            SELECT files.id as id, name, relpath, size, mtime, sha256, updated
                FROM files INNER JOIN folders ON files.folder = folders.id
                WHERE name=:filename AND
                      folder=(SELECT id FROM folders WHERE relpath=:folder);
        """).strip()
        path = Path(path)
        try:
            relpath = path.relative_to(self.root)
        except ValueError:
            message = f"Given path not under '{self.root!s}': {path}"
            raise NotUnderRoot(message) from None
        folder = str(relpath.parent)
        cursor = self.connection.cursor()
        cursor.execute(query, {'folder':  folder, 'filename': relpath.name})
        row = cursor.fetchone()
        if row is None:
            return None
        data = dict(row)
        return data

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
            size            INTEGER,                -- File's size in bytes
            mtime           INTEGER,                -- File's contents changed
            sha256          BLOB,                   -- Binary sha256 hash
            updated         INTEGER,                -- This record last updated
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

    def _do_add(self, cursor, file_):
        relpath = file_.relative_to(self.root)
        folder, filename = os.path.split(relpath)

        cursor.execute("INSERT OR IGNORE INTO folders(relpath) VALUES (?)", (folder,))
        cursor.execute("SELECT id FROM folders WHERE relpath=?;", (folder,))
        folder_id = cursor.fetchone()['id']

        # Build parameters
        parameters = {
            'name': file_.name,
            'size': file_.size,
            'mtime': file_.mtime,
            'folder': folder_id,
            'sha256': file_.sha256,
        }

        # Create bare file
        query = "INSERT OR IGNORE INTO files (name, folder) VALUES (:name, :folder);"
        cursor.execute(query, parameters)

        # Update file
        # (We do this in two steps to preserve the file's rowid. Running a single
        # 'INSERT OR REPLACE' increments that.)
        query = textwrap.dedent("""
            UPDATE files SET
                size=:size, mtime=:mtime, sha256=:sha256, updated=strftime('%s')
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
