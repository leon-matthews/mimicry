
import logging
from pprint import pprint as pp

from .database import DB
from .tree import Tree


logger = logging.getLogger(__name__)


class Updater:
    """
    Create and update the metadata database.
    """
    db_file = 'mimicry.db'

    def __init__(self, root):
        self.root = root.resolve()
        self.db_path = self.root / self.db_file

    def update(self):
        # Create database
        logger.debug(f"Create database: '{self.db_path}'")
        self.db = DB(self.db_path)

        # Create file tree
        logger.debug(f"Examine file system from: '{self.root}'")
        ignored = self.build_ignored_set()
        pp(ignored)
        self.tree = Tree(self.root, show_hidden=False, ignore=ignored)
        logger.debug(
            f"Found: {self.tree.total_files:,} files, "
            f"{self.tree.total_bytes:,} bytes")

        # Kill orphans
        # TODO

        # Update files
        self.update_files()

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

    def update_files(self):
        """
        Update (or create) records for every file under root.
        """
        num_updated = 0
        for file_ in self.tree.files():
            self.db.add(file_)
            num_updated += 1
        logger.info(f"Updated records for {num_updated:,} files")
