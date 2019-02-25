
from collections import namedtuple
import hashlib
import logging
import os.path
import sqlite3
import textwrap

from .models import File


logger = logging.getLogger(__name__)


File = namedtuple('File', 'name path relpath bytes mtime updated sha256 hashed')


class DB:
    """
    Database to store file metadata.
    """
    def __init__(self, path):
        """
        Create or open database file with given path.
        """
        self.path = os.path.abspath(path)
        self.folder = os.path.dirname(path)
        self.connection = sqlite3.connect(path, isolation_level=None)
        self.connection.row_factory = sqlite3.Row
        # ~ self.connection.set_trace_callback(print)
        self._create_schema()
        self._run_pragmas()

    def add(self, path):
        """
        Read single file with given path to the database.
        """
        def do_add(path, cursor):
            relpath = os.path.relpath(path, self.folder)
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
            #'INSERT OR REPLACE' query would increment that.
            query = textwrap.dedent("""
                UPDATE files SET
                    bytes=:bytes, mtime=:mtime, sha256=:sha256,
                    hashed=strftime('%s'), updated=strftime('%s')
                    WHERE name=:name AND folder=:folder;
            """).strip()
            cursor.execute(query, parameters)

        # Wrap
        cursor = self.connection.cursor()
        cursor.execute('SAVEPOINT add_file;')
        try:
            do_add(path, cursor)
            added = self.get(path)
            cursor.execute("RELEASE add_file;")
        except sqlite3.Error:
            cursor.execute("ROLLBACK TO add_file;")
            raise

        return added

    def get(self, path):
        """
        Return a single file record.
        """
        path = os.path.abspath(path)
        relpath = os.path.relpath(path, self.folder)
        folder, filename = os.path.split(relpath)
        query = textwrap.dedent("""
            SELECT name, bytes, mtime, updated, sha256, hashed
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
        data['path'] = path
        data['relpath'] = relpath
        data['sha256'] = data['sha256'].hex()
        return File(**data)

    def bytes(self):
        """
        Return sum of the bytes accross of all file records.
        """
        cursor = self.connection.execute("SELECT sum(bytes) FROM files;")
        return cursor.fetchone()[0]

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
        for row in self.connection.execute("SELECT * FROM files WHERE sha256 IN "
            "(SELECT sha256 FROM files GROUP BY sha256 HAVING count(*) > 1);"):
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
            data['path'] = os.path.join(self.folder, data['relpath'])
            data['sha256'] = data['sha256'].hex()
            yield File(**data)

    def _calculate_hash(self, path):
        BUFFSIZE = 4096 * 1000
        sha256 = hashlib.sha256()
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(BUFFSIZE), b''):
                sha256.update(chunk)
        return sha256.digest()

    def _create_schema(self):
        """
        Create database structure.

        All times are Unix epoch's.

        Should only be run on an empty database file.
        """
        schema = textwrap.dedent("""

        CREATE TABLE IF NOT EXISTS files (
            -- List of all files under database file.
            id      INTEGER PRIMARY KEY,
            name    TEXT NOT NULL,          -- File's name
            bytes   INTEGER,                -- File's size
            mtime   INTEGER,                -- File's mtime
            updated INTEGER,                -- Time metadata last updated
            sha256  BLOB,                   -- Binary sha256 hash
            hashed  INTEGER,                -- Time hash was last calculated
            folder  INTEGER NOT NULL,       -- Link to parent folder
            FOREIGN KEY(folder) REFERENCES folders(id),
            UNIQUE  (name, folder)
        );

        CREATE TABLE IF NOT EXISTS folders (
            -- List of all folders found under database file
            id      INTEGER PRIMARY KEY,
            relpath TEXT UNIQUE NOT NULL    -- Path relative to database
        );

        CREATE TABLE IF NOT EXISTS metadata (
            -- Single entry table containing DB metadata
            id      INTEGER PRIMARY KEY,
            label   TEXT NOT NULL,          -- Device label
            created INTEGER NOT NULL,       -- Database creation time
            updated INTEGER NOT NULL,       -- Time of completed update
            CHECK (rowid=1)                 -- Only one row allowed
        );

        """)
        self.connection.executescript(schema)
        self.connection.commit()

    def _run_pragmas(self):
        """
        Configure database connection.
        """
        cursor = self.connection.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")
        cursor.execute("PRAGMA synchronous = OFF;")
