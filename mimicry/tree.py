
import logging
import os
from pathlib import Path
from pprint import pprint as pp
from time import perf_counter

from .exceptions import NotAFolder
from .file import File
from .utils import normalise


logger = logging.getLogger(__name__)


class Tree:
    """
    Tree of folders and files under given root.
    """
    def __init__(self, root, show_hidden=False, ignore=None):
        """
        Initialiser.

        Args:
            root (str):
                Full path to root folder.
            show_hidden (bool):
                Show files and folders starting with full-stop. Defaults to `False`.
            ignore (set):
                Optional set of paths (relative to given root) to ignore. Not
                very featureful, but only really intended to skip our own
                database files (ie. sqlite3 and '.wal' and '.shm' files)
        """
        self.root = self._clean_root(root)
        self.show_hidden = show_hidden
        self.ignore = self._build_ignore_set(ignore)
        self.total_files = None
        self.total_bytes = None
        self._calculate_totals()

    def files(self):
        """
        Generator over all files under Tree's root, top-down order.
        """
        for name, path, rootfd in self._walk():
            yield File(path)

    def __repr__(self):
        root = str(self.root)
        root = root if root.endswith('/') else root + '/'
        return f"{self.__class__.__name__}('{root}')"

    def __str__(self):
        root = str(self.root)
        root = root if root.endswith('/') else root + '/'
        return f"{root}: {self.total_files:,} files, {self.total_bytes:,} bytes"

    def _build_ignore_set(self, ignore):
        """
        Build a set of full paths to ignore.
        """
        if ignore is None:
            ignore = []
        ignore_set = set()
        for relpath in ignore:
            ignore_set.add(os.path.join(self.root, relpath))
        return ignore_set

    def _calculate_totals(self):
        """
        Update count of files and file sizes.

        For speed, we avoid creating `File` objects by-passing the `files()` method.
        """
        logger.debug("Calculate file tree totals under: %s", self.root)
        self.total_files = 0
        self.total_bytes = 0
        started = perf_counter()
        for name, path, rootfd in self._walk(sort=False):
            s = os.lstat(name, dir_fd=rootfd)
            self.total_files += 1
            self.total_bytes += s.st_size
        elapsed = perf_counter() - started
        logger.info(
            f"Calculated file tree totals for {self.total_files} files "
            f"in {elapsed:.3f} seconds")

    def _clean_root(self, root):
        root = Path(root).expanduser().resolve(strict=False)
        if not root.is_dir():
            raise NotAFolder(f"Given root not a folder: '{root!s}'")
        return root

    def _walk(self, sort=True):
        """
        Yield tuple for every file under root, skipping hidden files if requested.

        Yields:
            3-tuple with file name, full-path, and open descriptor to folder.
        """
        for root, dirs, files, rootfd in os.fwalk(self.root, follow_symlinks=False):
            # Skip hidden folders?
            if not self.show_hidden:
                for index, name in enumerate(dirs):
                    if name.startswith('.'):
                        path = os.path.join(root, dirs[index])
                        logger.debug("Skipping hidden folder: %s", path)
                        del dirs[index]

            # Sort
            if sort:
                dirs.sort(key=normalise)
                files.sort(key=normalise)

            # Check files
            for name in files:
                path = os.path.join(root, name)

                # Skip hidden files?
                if (not self.show_hidden) and name.startswith('.'):
                    logger.debug("Skipping hidden file: %s", path)
                    continue

                # Skip ignored files
                if path in self.ignore:
                    logger.debug("Skipping ignored path: %s", path)
                    continue

                yield (name, path, rootfd)
