
import logging
import os
from pathlib import Path
from pprint import pprint as pp

from .exceptions import NotAFolder
from .file import File


logger = logging.getLogger(__name__)


class Tree:
    """
    Tree of folders and files under given root.
    """
    def __init__(self, root, show_hidden=False):
        """
        Initialiser.

        Args:
            root (str):
                Full path to root folder.
            show_hidden (bool):
                Show files and folders starting with full-stop. Defaults to `False`.
        """
        self.root = self._clean_root(root)
        self.show_hidden = show_hidden

        self.total_files = None
        self.total_bytes = None
        self._calculate_totals()

    def files(self):
        """
        Generator over all files under Tree's root, top-down order.
        """
        for name, root, rootfd in self._walk():
            yield File(os.path.join(root, name))

    def __repr__(self):
        return f"{self.__class__.__name__}({self.root!r})"

    def __str__(self):
        root = self.root if self.root.endswith('/') else self.root + '/'
        return f"{root}: {self.total_files:,} files, {self.total_bytes:,} bytes"

    def _calculate_totals(self):
        """
        Update count of files and file sizes.

        For speed, we by-pass the `files()` method.
        """
        self.total_files = 0
        self.total_bytes = 0
        for name, root, rootfd in self._walk():
            s = os.lstat(name, dir_fd=rootfd)
            self.total_files += 1
            self.total_bytes += s.st_size

    def _clean_root(self, root):
        root = os.path.expanduser(root)
        root = os.path.abspath(root)
        if not os.path.isdir(root):
            raise NotAFolder(f'Given root not a folder: {root!r}')
        return root

    def _walk(self):
        """
        Yield tuple for every file under root, skipping hidden files if requested.

        Yields:
            3-tuple with file name, folder, and open folder descriptor.
        """
        for root, dirs, files, rootfd in os.fwalk(self.root, follow_symlinks=False):
            # Skip hidden folders?
            if not self.show_hidden:
                for index, name in enumerate(dirs):
                    if name.startswith('.'):
                        del dirs[index]

            for name in files:
                # Skip hidden files
                if not self.show_hidden and name.startswith('.'):
                    continue

                yield (name, root, rootfd)
