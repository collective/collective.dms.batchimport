# -*- coding: utf-8 -*-

from collective.dms.batchimport.batchimport import BatchImporter
from collective.dms.batchimport.batchimport import ISettings
from collective.dms.batchimport.testing import INTEGRATION
from plone.app.testing import login
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME
from plone.registry.interfaces import IRegistry
from zope.component import getUtility

import json
import os
import tempfile
import unittest


class TestBatchImporter(unittest.TestCase):

    layer = INTEGRATION

    def setUp(self):
        self.app = self.layer["app"]
        self.portal = self.layer["portal"]
        self.request = self.layer["request"]
        self.registry = getUtility(IRegistry)
        self.settings = self.registry.forInterface(ISettings)
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        login(self.portal, TEST_USER_NAME)

        self.tmp_in = tempfile.TemporaryDirectory()
        self.tmp_out = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp_in.cleanup)
        self.addCleanup(self.tmp_out.cleanup)

        self.settings.fs_root_directory = self.tmp_in.name
        self.settings.processed_fs_root_directory = self.tmp_out.name
        self.settings.code_to_type_mapping = [
            {"code": "123", "portal_type": "dmsincomingmail"}
        ]

    def _write(self, path, data, mode="wb"):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, mode) as f:
            f.write(data)

    def test_call(self):
        meta_path = os.path.join(self.tmp_in.name, "123-foo.metadata")
        file_from_meta_path = os.path.join(self.tmp_in.name, "123-foo")
        plain_file_path = os.path.join(self.tmp_in.name, "123-bar.pdf")
        self._write(meta_path, json.dumps({"title": "Foo"}).encode("utf-8"))
        self._write(file_from_meta_path, b"DATA1")
        self._write(plain_file_path, b"DATA2")

        view = BatchImporter(self.portal, self.request)
        result = view()
        self.assertTrue(result.startswith("OK (2 imported files, 0 unprocessed files)"))
        self.assertTrue(
            os.path.exists(os.path.join(self.tmp_out.name, "123-foo.metadata"))
        )
        self.assertTrue(os.path.exists(os.path.join(self.tmp_out.name, "123-foo")))
        self.assertTrue(os.path.exists(os.path.join(self.tmp_out.name, "123-bar.pdf")))
        self.assertFalse(os.path.exists(meta_path))
        self.assertFalse(os.path.exists(file_from_meta_path))
        self.assertFalse(os.path.exists(plain_file_path))

    def test_call_returns_error(self):
        self.settings.fs_root_directory = ""
        view = BatchImporter(self.portal, self.request)
        result = view()
        self.assertEqual(result, "ERROR")

        absent_folder = os.path.join(self.tmp_in.name, "absent")
        self.settings.fs_root_directory = absent_folder
        result = view()
        self.assertEqual(result, "ERROR")
