
import hashlib
from pathlib import Path
from pprint import pprint as pp

from typing import Optional

from .exceptions import NotAbsolute, NotAFile
from .utils import file_size


class File:
    """
    Interface to an actual file on the current file system.
    """
    def __init__(self, path: Path):
        """
        Initialiser.

        Args:
            path: Path to file
        """
        # Check path
        path = Path(path)
        if not path.is_absolute():
            raise NotAbsolute(path)
        path = path.resolve()
        if not path.exists():
            raise NotAFile(path)
        self.path = path

        # Cached attributes
        self._mtime: Optional[float] = None
        self._sha256: Optional[bytes] = None
        self._size: Optional[int] = None

    @property
    def mtime(self) -> float:
        if self._mtime is None:
            self._update_stat()
        assert self._mtime is not None
        return self._mtime

    @property
    def name(self) -> str:
        return self.path.name

    def relative_to(self, root: Path) -> str:
        return str(self.path.relative_to(root))

    @property
    def sha256(self) -> bytes:
        """
        Calculate and return file's SHA256 hash.

        Returns (bytes): SHA256 binary hash of file's contents.
        """
        if self._sha256 is None:
            self._update_sha256()
        assert self._sha256 is not None
        return self._sha256

    @property
    def size(self) -> int:
        if self._size is None:
            self._update_stat()
        assert self._size is not None
        return self._size

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}('{self.path!s}')"

    def __str__(self) -> str:
        size = file_size(self.size)
        return f"{self.name} ({size})"

    def _update_sha256(self) -> None:
        BUFFSIZE = 4096 * 1024
        sha256 = hashlib.sha256()
        with open(self.path, 'rb') as f:
            for chunk in iter(lambda: f.read(BUFFSIZE), b''):
                sha256.update(chunk)
        self._sha256 = sha256.digest()

    def _update_stat(self) -> None:
        stat = self.path.stat()
        self._mtime = stat.st_mtime
        self._size = stat.st_size
