

import logging
import os

from .exceptions import NotAFolder


logger = logging.getLogger(__name__)


class Tree:
    """
    Interface to the tree of folders and files under root.
    """
    def __init__(self, root):
        self.root = self._check_root(root)
        self.total_files = None
        self.total_bytes = None
        self.calculate_totals()

    def calculate_totals(self):
        """
        Update count of files and file sizes.
        """
        self.total_files = 0
        self.total_bytes = 0
        for f in self.files():
            self.total_files += 1
            self.total_bytes += f.st_size

    def files(self):
        """
        Yield an `os.stat_result` record for every file under root.
        """
        for root, dirs, files, rootfd in os.fwalk(self.root, follow_symlinks=False):
            for name in files:
                try:
                    s = os.lstat(name, dir_fd=rootfd)
                    yield s
                except FileNotFoundError:
                    path = os.path.join(root, name)
                    raise

    def __repr__(self):
        return f"{self.__class__.__name__}({self.root!r})"

    def __str__(self):
        root = self.root if self.root.endswith('/') else self.root + '/'
        return f"{root}: {self.total_files:,} files, {self.total_bytes:,} bytes"

    def _check_root(self, root):
        root = os.path.expanduser(root)
        root = os.path.abspath(root)
        if not os.path.isdir(root):
            raise NotAFolder(f'Given root not a folder: {root!r}')
        return root
