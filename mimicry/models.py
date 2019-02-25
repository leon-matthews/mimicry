
import binascii
import hashlib
import os
import textwrap
import time


class File:
    """
    Represent a single file.

    path
        Optional.  If given, object will initialise itself from files metadata.
    fields
        Optional.  If given, object will initialise itself dictionary.
    """
    def __init__(self, path=None, fields=None):
        """
        Populates and stores its own metadata from given path.
        """
        if fields:
            self.path = fields['path']
            self.size = fields['size']
            self.mtime = fields['mtime']
            self.sha256 = fields['sha256']
            self.updated = fields['updated']
        elif path:
            self.from_file(path)
        else:
            self.path = None
            self.size = 0
            self.mtime = None
            self.sha256 = None
            self.updated = None

    def get_sha256(self):
        """
        Return the (normally binary) sha256 hash as hexadecimal string.
        """
        if self.sha256:
            return binascii.hexlify(self.sha256).decode('ascii')
        else:
            return ''

    def from_file(self, path, calculate_hash=False):
        """
        Initialise data from file.

        calculate_hash
            If True also reads file and calculates sha256 hash.
        """
        path = os.path.abspath(path)
        assert os.path.isfile(path), "File expected: '{}'".format(path)
        self.path = path
        stat = os.stat(self.path)
        self.mtime = int(stat.st_mtime)
        self.size = int(stat.st_size)
        self.sha256 = None
        self.updated = int(time.time())

        BUFFSIZE = 4096 * 1000
        if calculate_hash:
            with open(self.path, 'rb') as f:
                sha256 = hashlib.sha256()
                while True:
                    buf = f.read(BUFFSIZE)
                    if not buf:
                        break
                    sha256.update(buf)
                self.sha256 = sha256.digest()

    def _format_epoch(self, epoch):
        """
        Return RFC 2822 compatible text representation of given Unix epoch.
        """
        format_string = "%a, %d %b %Y %H:%M:%S +0000"
        return time.strftime(format_string, time.gmtime(epoch))

    def __repr__(self):
        return "<{}: {}>".format(self.__class__.__name__, self.path)

    def __str__(self):
        fields = vars(self)
        fields['sha256'] = self.get_sha256()
        fields['mtime'] = self._format_epoch(self.mtime)
        fields['updated'] = self._format_epoch(self.updated)
        s = textwrap.dedent("""
        {path}
            mtime:   {mtime}
            size:    {size:,} bytes
            sha256:    {sha256}
            updated: {updated}
        """).format(**fields)
        return s
