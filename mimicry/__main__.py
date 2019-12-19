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

from .updater import Updater


def main(path):
    root = Path(path)
    updater = Updater(root)
    updater.update()


def setup_logging():
    logging.basicConfig(level=logging.DEBUG)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        program_name = os.path.basename(os.path.dirname(sys.argv[0]))
        print("usage: {} PATH".format(program_name))
        sys.exit(1)

    setup_logging()
    main(sys.argv[1])
