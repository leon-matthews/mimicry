
import logging

from .database import DB
from .tree import Tree


logger = logging.getLogger(__name__)


class Updater:
    def __init__(self, root):
        self.root = root.resolve()
        self.db_path = root / 'mimicry.db'

    def update(self):
        logger.debug(f"Create database: '{self.db_path}'")
        self.db = DB(self.db_path)

        logger.debug(f"Examine file system from: '{self.root}'")
        self.tree = Tree(self.root)
        logger.debug(
            f"Found: {self.tree.total_files:,} files, "
            f"{self.tree.total_bytes:,} bytes")
        self.update_files()

    def update_files(self):
        """
        Update (or create) records for every file under root.
        """
        num_updated = 0
        for file_ in self.tree.files():
            self.db.add(file_)
            num_updated += 1
        logger.info(f"Updated records for {num_updated:,} files")
