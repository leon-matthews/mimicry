"""
Store file metadata in database.
"""

import collections
import os
import sqlite3
import textwrap

from .file import File


class DB:
    """
    Database to store file metadata.

    path
        Path to sqlite3 file to use.  Will be created if it doesn't exist.
        If no path is provided, an in-memory database will be used.
    """
    def __init__(self, path=None):
        """
        Create database file with given path.

        path
            Path to sqlite3 file
        """
        if path is None:
            path = ':memory:'
        exists = os.path.exists(path)
        self.connection = sqlite3.connect(path)
        self.connection.execute('PRAGMA synchronous = OFF;')
        self.connection.row_factory = sqlite3.Row
        if not exists:
            self._create_schema()

    def count_bytes(self):
        """
        Return sum of the sizes of all file records.
        """
        cursor = self.connection.execute("SELECT sum(size) FROM files;")
        num_bytes = cursor.fetchone()[0]
        return 0 if num_bytes is None else num_bytes

    def count(self):
        """
        Return the total number of file records.
        """
        cursor = self.connection.execute("SELECT count(*) FROM files;")
        return cursor.fetchone()[0]

    def delete(self, path):
        """
        Delete the file record with the given path.
        """
        path = os.path.abspath(path)
        self.connection.execute('DELETE FROM files WHERE path=?;', (path,))
        self.connection.commit()

    def duplicates(self):
        """
        Iterate over duplicate files.
        """
        duplicates = collections.defaultdict(list)
        for row in self.connection.execute("SELECT * FROM files WHERE sha1 IN "
            "(SELECT sha1 FROM files GROUP BY sha1 HAVING count(*) > 1);"):
            f = File(fields=row)
            duplicates[f.sha1].append(f)
        return duplicates

    def files(self):
        """
        Iterate over every file in database.
        """
        for row in self.connection.execute('SELECT * FROM files;'):
            yield File(fields=row)

    def save(self, f):
        """
        Create or update given File object's record
        """
        self.connection.execute(
            'INSERT OR REPLACE INTO files VALUES (?, ?, ?, ?, ?)',
            (f.path, f.size, f.mtime, f.sha1, f.updated))
        self.connection.commit()

    def load(self, path):
        """
        Load a single File object with given path.

        Returns None if no row found.
        """
        path = os.path.abspath(path)
        cursor = self.connection.execute(
            'SELECT * FROM files WHERE path=?;', (path,))
        row = cursor.fetchone()
        if row is None:
            return None
        return File(fields=row)

    def _create_schema(self):
        """
        Create database structure.

        Should only be run on an empty database file.
        """
        schema = textwrap.dedent("""

        CREATE TABLE files (
            path    TEXT UNIQUE NOT NULL,   -- Absolute path
            size    INTEGER NOT NULL,       -- Size in bytes
            mtime   INTEGER NOT NULL,       -- Unix epoch
            sha1    BLOB,                   -- Binary SHA1 hash
            updated INTEGER NOT NULL        -- Unix epoch when record updated
        );

        CREATE INDEX files_sha1_index on files(sha1);

        """)
        self.connection.executescript(schema)
        self.connection.commit()
