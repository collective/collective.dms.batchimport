# -*- coding: utf-8 -*-

from imio.pyutils.system import error
from imio.pyutils.system import verbose

import argparse
import sys


def add_metadata():
    """Add metadata file and/or metadata attribute"""
    parser = argparse.ArgumentParser(description="Add metadata file and/or metadata attribute")
    parser.add_argument("import_directory", help="Import directory")
    ns = parser.parse_args()
    verbose("Start of %s" % sys.argv[0])
    verbose("End of %s" % sys.argv[0])
