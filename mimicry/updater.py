
import logging
from pprint import pprint as pp
from time import perf_counter
from typing import List

from .database import DB, FileRecord
from .tree import Tree
from .utils import file_size


logger = logging.getLogger(__name__)


class Updater:
    """
    Create and update the metadata database.
    """
    db_file = 'mimicry.db'

    def __init__(self, root):
        self.root = root.resolve()
        self.db_path = self.root / self.db_file
        self.db = None

    def update(self):
        # Create and/or load database
        logger.debug(f"Create database: '{self.db_path}'")
        self.db = DB(self.db_path)

        # Create file tree
        ignored = self.build_ignored_set()
        files = self.read_files(ignored)

        # Kill orphans
        records = self.read_records()
        orphans = self.find_orphans(records, files)
        if orphans:
            logger.info(f"Delete {len(orphans):,} orphaned records from database")
        for orphan in orphans:
            self.db.delete(self.root / orphan)

        # Update database
        self.update_records(files)

    def build_ignored_set(self):
        """
        Build set of paths to ignore
        """
        # Ignore own database files
        ignored = set()
        path = str(self.db_path)
        ignored.add(path)
        for suffix in ('-wal', '-shm'):
            ignored.add(path + suffix)
        return ignored

    def find_orphans(self, existing, tree) -> List[FileRecord]:
        """
        Find all orphaned database records.

        If a file has been deleted from disk its record is now orphaned
        and should be deleted.
        """
        orphans = list(existing.keys() - tree.keys())
        return orphans

    def read_records(self):
        """
        Read every database record into a dictionary, keyed by relpath.
        """
        logger.debug(f"Load records from database")
        started = perf_counter()
        existing = {record.relpath: record for record in self.db.files()}
        elapsed = perf_counter() - started
        logger.info(
            f"Loaded {len(existing):,} records from "
            f"database in {elapsed:.3f} seconds")
        return existing

    def read_files(self, ignored):
        """
        Read metadata about every file in root into a dictionary, keyed by relpath.
        """
        logger.debug(f"Load files from file tree")
        tree = Tree(self.root, show_hidden=False, ignore=ignored)
        files = {}
        started = perf_counter()
        for file_ in tree.files():
            relpath = file_.relative_to(self.root)
            files[relpath] = file_
        elapsed = perf_counter() - started
        total_size = file_size(tree.total_bytes, traditional=True)
        logger.info(
            f"Loaded {len(files):,} files ({total_size}) from "
            f"file system in {elapsed:.3f} seconds")
        return files

    def update_records(self, files):
        """
        Update (or create) records for every file under root.
        """
        num_updated = 0
        for relpath in files:
            file_ = files[relpath]
            self.db.add(file_)
            num_updated += 1
        logger.info(f"Updated records for {num_updated:,} files")
