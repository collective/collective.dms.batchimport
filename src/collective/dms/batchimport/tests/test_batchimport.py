from collective.dms.batchimport.batchimport import BatchImportError
from collective.dms.batchimport.batchimport import ISettings
from collective.dms.batchimport.testing import INTEGRATION
from datetime import datetime
from plone import api
from plone.app.testing import login
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.registry.interfaces import IRegistry
from zope.component import getMultiAdapter
from zope.component import getUtility
from zope.testing.loggingsupport import InstalledHandler

import json
import os
import shutil
import tempfile
import unittest


class TestBatchImporter(unittest.TestCase):

    layer = INTEGRATION

    def setUp(self):
        self.portal = self.layer["portal"]
        self.request = self.layer["request"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        # createDocument adopts the current user by its id: a user whose login is its id, as in iA.Docs
        api.user.create(
            email="importer@example.com", username="importer", password="Import!123"
        )
        setRoles(self.portal, "importer", ["Manager"])
        login(self.portal, "importer")
        api.content.create(
            container=self.portal, type="Folder", id="incoming", title="Incoming"
        )
        api.content.create(
            container=self.portal, type="Folder", id="outgoing", title="Outgoing"
        )
        self.import_dir = tempfile.mkdtemp()  # Plone 6: str, no six
        self.processed_dir = tempfile.mkdtemp()  # Plone 6: str, no six
        self.addCleanup(shutil.rmtree, self.import_dir)
        self.addCleanup(shutil.rmtree, self.processed_dir)
        self.settings = getUtility(IRegistry).forInterface(ISettings)
        self.settings.fs_root_directory = self.import_dir
        self.settings.processed_fs_root_directory = self.processed_dir
        self.settings.code_to_type_mapping = [
            {"code": "123", "portal_type": "dmsincomingmail"},
            {"code": "456", "portal_type": "dmsdocument"},
        ]
        self.view = getMultiAdapter((self.portal, self.request), name="batchimport")
        self.log = InstalledHandler("collective.dms.batchimport")
        self.addCleanup(self.log.uninstall)

    def write(self, path, data=b"%PDF-1.4 scan"):
        """Write a file of the import directory (path relative to it)"""
        path = os.path.join(self.import_dir, path)
        if not os.path.exists(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path))
        with open(path, "wb") as fh:
            fh.write(data)
        return path

    def write_metadata(self, path, metadata):
        return self.write(path, json.dumps(metadata).encode("utf8"))

    def prepare_view(self):
        """Attributes set by __call__, for the methods called alone"""
        self.view.fs_root_directory = self.import_dir + "/"
        self.view.processed_fs_root_directory = self.processed_dir + "/"
        self.view.code_to_type_mapping = {
            "123": "dmsincomingmail",
            "456": "dmsdocument",
        }

    def warnings(self):
        return [
            record.getMessage()
            for record in self.log.records
            if record.levelname == "WARNING"
        ]

    def test_call(self):
        # no import directory: nothing is imported
        self.settings.fs_root_directory = None
        self.assertEqual(self.view(), "ERROR")
        self.settings.fs_root_directory = os.path.join(self.import_dir, "missing")
        self.assertEqual(self.view(), "ERROR")
        self.assertEqual(
            self.warnings(),
            [
                "settings.fs_root_directory is not defined",
                "settings.fs_root_directory do not exist",
            ],
        )
        self.settings.fs_root_directory = self.import_dir
        self.assertEqual(self.view(), "OK (0 imported files, 0 unprocessed files)")

        # a scanner output: files named <code>-<title>, optional .metadata json sidecar files,
        # sub-directories mapped to site folders, dot files and directories skipped
        self.write("123-Letter 10.pdf", b"letter 10")
        self.write("123-Letter 9.pdf", b"letter 9")
        self.write("123-Réponse.pdf", b"reponse")  # codespell:ignore reponse
        self.write("456-Scan.pdf", b"scan")
        self.write_metadata(
            "456-Scan.pdf.metadata",
            {"title": "Invoice", "description": "From the supplier"},
        )
        self.write("incoming/123-Complaint.pdf", b"complaint")
        self.write(".hidden.pdf")
        self.write(".git/123-Ignored.pdf")
        self.assertEqual(self.view(), "OK (5 imported files, 0 unprocessed files)")
        self.assertEqual(self.warnings()[2:], [])

        # documents: metadata files first, then the other files in natural order
        docs = [
            obj
            for obj in self.portal.objectValues()
            if obj.portal_type in ("dmsincomingmail", "dmsdocument")
        ]
        self.assertEqual(
            [doc.id for doc in docs],
            ["invoice", "letter-9", "letter-10", "reponse"],  # codespell:ignore reponse
        )
        invoice = docs[0]
        self.assertEqual(invoice.portal_type, "dmsdocument")
        self.assertEqual(invoice.title, "Invoice")
        self.assertEqual(invoice.description, "From the supplier")
        letter = self.portal["letter-9"]
        self.assertEqual(letter.portal_type, "dmsincomingmail")
        self.assertEqual(letter.title, "Letter 9")
        self.assertEqual(letter.Creator(), "importer")
        self.assertEqual(letter.getOwner().getId(), "importer")
        self.assertTrue(letter.internal_reference_no)
        self.assertIsInstance(letter.reception_date, datetime)
        self.assertEqual(
            self.portal["reponse"].title, "Réponse"  # codespell:ignore reponse
        )  # codespell:ignore reponse
        self.assertEqual(self.portal["incoming"].objectIds(), ["complaint"])
        # the main file: the file data, the filename without its code
        self.assertEqual(letter.objectIds(), ["scanned-mail"])
        main_file = letter["scanned-mail"]
        self.assertEqual(main_file.portal_type, "dmsmainfile")
        self.assertEqual(main_file.title, "Scanned Mail")
        self.assertEqual(main_file.file.data, b"letter 9")
        self.assertEqual(main_file.file.filename, "Letter 9.pdf")
        self.assertEqual(invoice["scanned-mail"].file.filename, "Scan.pdf")

        # imported files are moved to the processed directory, with their directory structure
        self.assertEqual(
            sorted(os.listdir(self.import_dir)), [".git", ".hidden.pdf", "incoming"]
        )
        self.assertEqual(os.listdir(os.path.join(self.import_dir, "incoming")), [])
        self.assertEqual(
            sorted(os.listdir(self.processed_dir)),
            [
                "123-Letter 10.pdf",
                "123-Letter 9.pdf",
                "123-Réponse.pdf",
                "456-Scan.pdf",
                "456-Scan.pdf.metadata",
                "incoming",
            ],
        )
        self.assertEqual(
            os.listdir(os.path.join(self.processed_dir, "incoming")),
            ["123-Complaint.pdf"],
        )

        # files that can't be imported are logged, counted and left in the import directory
        self.write("999-Unknown code.pdf")
        self.write("archives/123-No folder.pdf")
        self.write("123-Letter 9.pdf")
        self.assertEqual(self.view(), "OK (0 imported files, 3 unprocessed files)")
        self.assertEqual(
            sorted(self.warnings()[2:]),
            [
                "error importing 123-Letter 9.pdf (document already exists)",
                "error importing 999-Unknown code.pdf (no portal type associated to this code '999')",
                "error importing archives/123-No folder.pdf (directory structure mismatch)",
            ],
        )
        self.assertEqual(
            sorted(os.listdir(self.import_dir)),
            [
                ".git",
                ".hidden.pdf",
                "123-Letter 9.pdf",
                "999-Unknown code.pdf",
                "archives",
                "incoming",
            ],
        )

        # same import and processed directories: imported files stay in place
        self.settings.processed_fs_root_directory = self.import_dir + "/"
        self.write("incoming/123-Claim.pdf")
        self.assertEqual(self.view(), "OK (1 imported files, 3 unprocessed files)")
        self.assertEqual(self.portal["incoming"].objectIds(), ["complaint", "claim"])
        self.assertEqual(
            os.listdir(os.path.join(self.import_dir, "incoming")), ["123-Claim.pdf"]
        )

    @unittest.expectedFailure
    def test_call_file_metadata(self):
        """file_* keys of a .metadata file are fields of the main file: RuntimeError on Plone 4 (Known issues)"""
        self.write("123-Scan.pdf")
        self.write_metadata(
            "123-Scan.pdf.metadata", {"title": "Invoice", "file_title": "Original scan"}
        )
        self.assertEqual(self.view(), "OK (1 imported files, 0 unprocessed files)")
        self.assertEqual(self.portal["invoice"]["original-scan"].title, "Original scan")

    @unittest.expectedFailure
    def test_call_unexpected_errors(self):
        """Other errors of a file aren't counted: they stop the import (Known issues)"""
        # duplicate internal reference number (Invalid)
        self.write("123-First.pdf")
        self.write_metadata(
            "123-First.pdf.metadata",
            {"title": "First", "internal_reference_no": "IN-1"},
        )
        self.write("incoming/123-Second.pdf")
        self.write_metadata(
            "incoming/123-Second.pdf.metadata",
            {"title": "Second", "internal_reference_no": "IN-1"},
        )
        self.assertEqual(self.view(), "OK (1 imported files, 1 unprocessed files)")
        # file name without code (ValueError)
        self.write("No code.pdf")
        self.assertEqual(self.view(), "OK (0 imported files, 2 unprocessed files)")
        # metadata file without its file (IOError)
        self.write_metadata("123-Lost.pdf.metadata", {"title": "Lost"})
        self.assertEqual(self.view(), "OK (0 imported files, 3 unprocessed files)")

    def test_mark_as_processed(self):
        self.prepare_view()
        path = self.write("incoming/2024/123-Letter.pdf")
        self.view.mark_as_processed(path)
        self.assertFalse(os.path.exists(path))
        self.assertTrue(
            os.path.exists(
                os.path.join(self.processed_dir, "incoming/2024/123-Letter.pdf")
            )
        )
        # same import and processed directories: not moved
        self.view.processed_fs_root_directory = self.view.fs_root_directory
        path = self.write("123-Other.pdf")
        self.view.mark_as_processed(path)
        self.assertTrue(os.path.exists(path))
        self.assertFalse(
            os.path.exists(os.path.join(self.processed_dir, "123-Other.pdf"))
        )

    def test_get_folder(self):
        self.assertEqual(self.view.get_folder(""), self.portal)
        self.assertEqual(self.view.get_folder("incoming"), self.portal["incoming"])
        api.content.create(container=self.portal["incoming"], type="Folder", id="2024")
        self.assertEqual(
            self.view.get_folder("incoming/2024"), self.portal["incoming"]["2024"]
        )
        self.assertEqual(
            self.view.get_folder("/incoming//2024/"), self.portal["incoming"]["2024"]
        )
        self.assertRaises(AttributeError, self.view.get_folder, "archives")

    @unittest.expectedFailure
    def test_get_folder_acquisition(self):
        """A missing sub-folder is acquired from a parent: wrong folder instead of a mismatch (Known issues)"""
        self.assertRaises(AttributeError, self.view.get_folder, "outgoing/incoming")

    def test_convertTitleToId(self):
        self.assertEqual(self.view.convertTitleToId("Letter 9"), "letter-9")
        self.assertEqual(
            self.view.convertTitleToId("Réponse à l'avis"),
            "reponse-a-lavis",  # codespell:ignore reponse
        )

    def test_import_one(self):
        self.prepare_view()
        # title from the file name, document in the folder of the directory
        path = self.write("incoming/123-Letter.pdf", b"letter")
        self.view.import_one(path, "incoming")
        letter = self.portal["incoming"]["letter"]
        self.assertEqual(letter.portal_type, "dmsincomingmail")
        self.assertEqual(letter.title, "Letter")
        self.assertEqual(letter["scanned-mail"].file.data, b"letter")
        # the file is not moved here (mark_as_processed)
        self.assertTrue(os.path.exists(path))
        # metadata: document fields, the id still comes from the title
        path = self.write("456-Scan.pdf")
        self.view.import_one(
            path, "", {"title": "Invoice", "description": "Supplier"}, {}
        )
        self.assertEqual(self.portal["invoice"].description, "Supplier")
        self.assertNotIn("scan", self.portal.objectIds())
        # errors
        with self.assertRaises(BatchImportError) as cm:
            self.view.import_one(path, "archives")
        self.assertEqual(str(cm.exception), "directory structure mismatch")
        path = self.write("999-Letter.pdf")
        with self.assertRaises(BatchImportError) as cm:
            self.view.import_one(path, "")
        self.assertEqual(
            str(cm.exception), "no portal type associated to this code '999'"
        )
        path = self.write("incoming/123-Letter.pdf")
        with self.assertRaises(BatchImportError) as cm:
            self.view.import_one(path, "incoming")
        self.assertEqual(str(cm.exception), "document already exists")
        path = self.write("No code.pdf")
        self.assertRaises(ValueError, self.view.import_one, path, "")

    @unittest.expectedFailure
    def test_import_one_acquired_id(self):
        """The existing document is looked up with acquisition: a parent with the same id blocks it (Known issues)"""
        self.prepare_view()
        self.view.import_one(self.write("incoming/123-Incoming.pdf"), "incoming")
        self.assertIn("incoming", self.portal["incoming"].objectIds())


class TestControlPanel(unittest.TestCase):

    layer = INTEGRATION

    def setUp(self):
        self.portal = self.layer["portal"]
        self.request = self.layer["request"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])

    def test_controlpanel(self):
        view = getMultiAdapter(
            (self.portal, self.request), name="batchimport-controlpanel"
        )
        html = view()
        self.assertIn("Batch Import Settings", html)
        for widget_id in (
            "fs_root_directory",
            "processed_fs_root_directory",
            "code_to_type_mapping",
        ):
            self.assertIn('id="form-widgets-%s"' % widget_id, html)
        self.assertIn("pat-datagridfield", html)  # Plone 6: datagridfield 4.x pattern
        # save: the registry records are updated
        self.request.form.update(
            {
                "form.widgets.fs_root_directory": "/srv/import",
                "form.widgets.processed_fs_root_directory": "/srv/processed",
                "form.widgets.code_to_type_mapping.0-empty-marker": "1",
                "form.widgets.code_to_type_mapping.0.widgets.code": "123",
                "form.widgets.code_to_type_mapping.0.widgets.portal_type": "dmsincomingmail",
                "form.widgets.code_to_type_mapping.count": "1",
                "form.buttons.save": "Save",
            }
        )
        view = getMultiAdapter(
            (self.portal, self.request), name="batchimport-controlpanel"
        )
        view()
        settings = getUtility(IRegistry).forInterface(ISettings)
        self.assertEqual(settings.fs_root_directory, "/srv/import")
        self.assertEqual(settings.processed_fs_root_directory, "/srv/processed")
        self.assertEqual(
            settings.code_to_type_mapping,
            [{"code": "123", "portal_type": "dmsincomingmail"}],
        )
