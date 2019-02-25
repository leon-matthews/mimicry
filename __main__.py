"""
Walk the file system, reading file metadata along the way.
"""

import os
import sys
import textwrap

from .db import DB
from .cache import Cache


if __name__ == '__main__':
    if len(sys.argv) != 2:
        program_name = os.path.basename(os.path.dirname(sys.argv[0]))
        print("usage: {} path".format(program_name))
        sys.exit(1)

    root = sys.argv[1]
    db_path = './files.db'

    c = Cache(db_path)

    print()
    print("Deleting obsolete records...")
    deleted = c.delete(dry_run=False)
    print("{:,} records deleted".format(deleted))

    print()
    print("Updating cache from file system...")
    files_updated = c.update(root)
    print("{:,} file records added".format(files_updated))

    stats = c.stats()
    print(textwrap.dedent(
        """
        {num_files:,} total file records
        {num_bytes:,} total bytes
        """.format(**stats)))
