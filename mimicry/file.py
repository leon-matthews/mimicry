
import hashlib
from pathlib import Path
from pprint import pprint as pp


class File:
    """
    Metadata for actual file.
    """
    def __init__(self, path):
        """
        Initialiser.

        Args:
            path: Path to file
        """
        self.path = Path(path).resolve()

        # Cached properties
        self._mtime = None
        self._sha256 = None
        self._size = None

    @property
    def mtime(self):
        if self._mtime is None:
            self._update_stat()
        return self._mtime

    @property
    def name(self):
        return self.path.name

    def relative_to(self, root):
        return self.path.relative_to(root)

    @property
    def sha256(self):
        """
        Calculate and return file's SHA256 hash.

        Returns (bytes): SHA256 binary hash of file's contents.
        """
        if self._sha256 is None:
            self._update_sha256()
        return self._sha256

    @property
    def size(self):
        if self._size is None:
            self._update_stat()
        return self._size

    def __repr__(self):
        return f"{self.__class__.__name__}('{self.path!s}')"

    def __str__(self):
        return f"{self.name}: {self.size:,} bytes"

    def _update_sha256(self):
        BUFFSIZE = 4096 * 1024
        sha256 = hashlib.sha256()
        with open(self.path, 'rb') as f:
            for chunk in iter(lambda: f.read(BUFFSIZE), b''):
                sha256.update(chunk)
        self._sha256 = sha256.digest()

    def _update_stat(self):
        stat = self.path.stat()
        self._mtime = stat.st_mtime
        self._size = stat.st_size
