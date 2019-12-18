#!/usr/bin/env python3

"""
Walk the file system, reading file metadata along the way.
"""

import logging
import os
from pathlib import Path
from pprint import pprint as pp
import sys
import textwrap

from .database import DB
from .tree import Tree


def setup_logging():
    logging.basicConfig(level=logging.DEBUG)


if __name__ == '__main__':
    setup_logging()

    if len(sys.argv) != 2:
        program_name = os.path.basename(os.path.dirname(sys.argv[0]))
        print("usage: {} PATH".format(program_name))
        sys.exit(1)

    root = Path(sys.argv[1]).resolve()
    tree = Tree(root)

    path = root / 'mimicry.db'
    db = DB(path)

    db.connection.execute("BEGIN;")
    for file_ in tree.files():
        db.add(file_)

    db.connection.execute("COMMIT;")

    sys.exit(0)

    print()
    print("Deleting obsolete records...")
    deleted = c.delete(dry_run=False)
    print("{:,} records deleted".format(deleted))

    print()
    print("Updating cache from file system...")
    files_updated = c.update(root)
    tree = Tree(root)
    print(str(tree))
    print("{:,} file records added".format(files_updated))

    stats = c.stats()
    print(textwrap.dedent(
        """
        {num_files:,} total file records
        {num_bytes:,} total bytes
        """.format(**stats)))
