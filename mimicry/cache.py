"""
Database of files' metadata and sha256 content hash.
"""

import logging
import os

from .database import DB
from .exceptions import NotAFolder


logger = logging.getLogger(__name__)


class Tree:
    """
    Represent a file-system tree.
    """
    def __init__(self, root):
        self.root = self._check_root(root)
        self.num_files = 0
        self.num_bytes = 0
        self.update()

    def update(self):
        """
        Update count of files and file sizes.
        """
        for root, dirs, files, rootfd in os.fwalk(self.root):
            self.num_files += len(files)
            for name in files:
                try:
                    s = os.stat(name, dir_fd=rootfd)
                except FileNotFoundError:
                    path = os.path.join(root, name)
                    if os.path.islink(path):
                        # Ignore broken symlinks
                        pass
                    else:
                        raise
                self.num_bytes += s.st_size

    def __repr__(self):
        return f"{self.__class__.__name__}({self.root!r})"

    def __str__(self):
        root = self.root if self.root.endswith('/') else self.root + '/'
        return f"{root}: {self.num_files:,} files, {self.num_bytes:,} bytes"

    def _check_root(self, root):
        root = os.path.expanduser(root)
        root = os.path.abspath(root)
        if not os.path.isdir(root):
            raise NotAFolder(f'Given root not a folder: {root!r}')
        return root


class Cache:
    """
    Provide interface to file system

    cache_path
        Path to SQLite3 file to use as cache database.
    """
    def __init__(self, cache_path):
        self.cache_path = cache_path
        self.db = DB(self.cache_path)

    def calculate_duplicates(self):
        """
        Return data structure containing files with duplicate sha256 sums.
        """
        return self.db.duplicates()

    def delete(self, dry_run=False):
        """
        Check all cache records, removing those for missing files.

        dry_run
            If True, don't actually delete any records, just show what *would*
            have been deleted.

        Returns number of records deleted.
        """
        # Iterate over every single path in the database
        num = 0
        for f in self.db.files():
            path = f.path
            if not os.path.exists(path):
                num += 1
                print("-{}".format(path))
                if not dry_run:
                    self.db.delete(path)
        return num

    def stats(self):
        """
        Returns dictionary containing statistics about cache.
        """
        return {
            'num_files': self.db.count(),
            'num_bytes': self.db.count_bytes(),
        }

    def update(self, root):
        """
        Update and create cache records for all files under given root.

        Returns number of file records updated.
        """
        files_updated = 0
        for root, dirs, files in os.walk(root):
            root = os.path.abspath(root)
            dirs.sort(key=str.lower)
            files.sort(key=str.lower)

            for name in files:
                path = os.path.join(root, name)
                logger.debug("Add %r", path)
                was_updated = self.db.add(path)
                if was_updated:
                    files_updated += 1

        return files_updated

    def _update_file(self, path):
        """
        Examines file in path, skipping re-calculating the sha256 hash if the
        name and mtime of the file are unchanged from the cache record.

        Returns True if file record was updated, False otherwise.
        """
        # Load file metadata from disk (without sha256 for now)
        local_file = File(path=path)

        # Compare file with file from cache.  Skip if mtime the same.
        try:
            cached_file = self.db.load(path)
        except UnicodeEncodeError:
            print(repr(path))
            raise
        if cached_file and cached_file.mtime == local_file.mtime:
            return False

        # Calculate hash, save to db
        print("+{}".format(path))
        local_file.from_file(path, calculate_hash=True)
        self.db.save(local_file)
        return True
