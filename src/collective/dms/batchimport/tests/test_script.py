from collective.dms.batchimport.script import add_metadata
from io import StringIO  # Plone 6: no six

import sys
import unittest


class TestScript(unittest.TestCase):
    def run_script(self, *args):
        """Run the console script with these arguments, return its output and error output"""
        argv, stdout, stderr = sys.argv, sys.stdout, sys.stderr
        sys.argv = ["batchimport_add_metadata"] + list(args)
        sys.stdout, sys.stderr = StringIO(), StringIO()
        try:
            add_metadata()
            return sys.stdout.getvalue(), sys.stderr.getvalue()
        finally:
            sys.argv, sys.stdout, sys.stderr = argv, stdout, stderr

    def test_add_metadata(self):
        # nothing is done yet: start and end messages only
        out, err = self.run_script("/srv/import")
        self.assertEqual(
            out,
            ">> Start of batchimport_add_metadata\n>> End of batchimport_add_metadata\n",
        )
        self.assertEqual(err, "")
        # the import directory is required
        with self.assertRaises(SystemExit) as cm:
            self.run_script()
        self.assertEqual(cm.exception.code, 2)
