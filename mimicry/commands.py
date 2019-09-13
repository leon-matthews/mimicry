

import logging
import os

from .database import DB


logger = logging.getLogger(__name__)


class Commands:
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
            'num_files': self.db.files_count(),
            'num_bytes': self.db.files_size(),
        }
