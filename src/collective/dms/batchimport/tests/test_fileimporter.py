# -*- coding: utf-8 -*-

from collective.dms.batchimport.fileimporter import ImportFileForm
from collective.dms.batchimport.testing import INTEGRATION
from plone.app.testing import login
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME
from plone.namedfile.file import NamedBlobFile
from unittest.mock import patch

import unittest


class TestFileImporter(unittest.TestCase):

    layer = INTEGRATION

    def setUp(self):
        self.app = self.layer["app"]
        self.portal = self.layer["portal"]
        self.request = self.layer["request"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        login(self.portal, TEST_USER_NAME)
        self.portal.invokeFactory("Folder", id="foo", title="foo")
        self.portal["foo"].invokeFactory("Folder", id="bar", title="bar")

    def test_get_folder(self):
        view = ImportFileForm(self.portal, self.request)
        folder = view.get_folder("foo/bar")
        self.assertEqual(folder, self.portal["foo"]["bar"])

    def test_convert_title_to_id(self):
        view = ImportFileForm(self.portal, self.request)
        self.assertEqual(view.convertTitleToId("Hello World"), "hello-world")
        self.assertEqual(view.convertTitleToId("éàâ Ç&%$"), "eaa-c")

    def test_import_file_success(self):
        view = ImportFileForm(self.portal, self.request)
        f = NamedBlobFile(data=b"DATA", filename="My Document.pdf")
        data = {
            "file": f,
            "title": None,
            "portal_type": "dmsincomingmail",
            "location": "foo/bar",
            "owner": "alice",
        }
        with patch.object(ImportFileForm, "extractData", return_value=(data, [])):
            with patch("collective.dms.batchimport.utils.createDocument") as create:
                view.import_file(view, action=None)
        args, kwargs = create.call_args
        self.assertEqual(args[1], self.portal["foo"]["bar"])
        self.assertEqual(args[2], "dmsincomingmail")
        self.assertEqual(args[3], "my-document")
        self.assertIs(args[4], f)
        self.assertEqual(args[5], "alice")

    def test_import_file_errors_sets_status_and_does_not_create(self):
        view = ImportFileForm(self.portal, self.request)
        f = NamedBlobFile(data=b"DATA", filename="x.pdf")
        data = {
            "file": f,
            "title": None,
            "portal_type": "dmsincomingmail",
            "location": "foo/bar",
            "owner": "alice",
        }
        with patch.object(
            ImportFileForm, "extractData", return_value=(data, [object()])
        ):
            with patch("collective.dms.batchimport.utils.createDocument") as create:
                view.import_file(view, action=None)
        self.assertEqual(create.call_count, 0)
        self.assertEqual(view.status, view.formErrorsMessage)
