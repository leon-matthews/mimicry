"""
Abstract a single file's metadata
"""

import binascii
import hashlib
import os
import textwrap
import time


class File:
    """
    File metadata storage and management.

    path
        Optional.  If given, object will initialise itself from files metadata.
    fields
        Optional.  If given, object will initialise itself dictionary.
    """
    def __init__(self, path=None, fields=None, read_sha1=True):
        """
        Populates and stores its own metadata from given path.
        """
        if fields:
            self.path = fields['path']
            self.size = fields['size']
            self.mtime = fields['mtime']
            self.sha1 = fields['sha1']
            self.updated = fields['updated']
        elif path:
            path = os.path.abspath(path)
            assert os.path.isfile(path), "File expected: '{}'".format(path)
            self.path = path
            self.update(read_sha1)
        else:
            self.path = None
            self.size = None
            self.mtime = None
            self.sha1 = None
            self.updated = None

    def format_sha1(self):
        """
        Return the  binary sha1 hash as hexadecimal string.
        """
        if self.sha1:
            return binascii.hexlify(self.sha1).decode('ascii')
        else:
            return None

    def update(self, read_sha1=True):
        """
        Update metadata from source file.

        read_sha1
            If True also reads file, calculating SHA1 hash.
        """
        stat = os.stat(self.path)
        self.mtime = int(stat.st_mtime)
        self.size = int(stat.st_size)
        self.sha1 = None
        self.updated = int(time.time())

        if read_sha1:
            self._calculate_sha1()

    def _calculate_sha1(self):
        """Calculate sha1 of file"""
        with open(self.path, 'rb') as f:
            sha1 = hashlib.sha1()
            while True:
                # Read only 4kB at a time
                buf = f.read(4096)
                if not buf:
                    break
                sha1.update(buf)
            self.sha1 = sha1.digest()

    def _format_epoch(self, epoch):
        """
        Return RFC 2822 compatible text representation of given Unix epoch.
        """
        format_string = "%a, %d %b %Y %H:%M:%S +0000"
        return time.strftime(format_string, time.gmtime(epoch))

    def __str__(self):
        """
        Multi-line string representation for debugging
        """
        # Make copy to avoid aliasing errors
        fields = dict(vars(self))
        fields['sha1'] = self.get_sha1()
        fields['mtime'] = self._format_epoch(self.mtime)
        fields['updated'] = self._format_epoch(self.updated)
        s = textwrap.dedent("""
        {path}
            mtime:   {mtime}
            size:    {size:,} bytes
            sha1:    {sha1}
            updated: {updated}
        """).format(**fields)
        return s
