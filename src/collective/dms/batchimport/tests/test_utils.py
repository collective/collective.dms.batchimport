from collective.dms.batchimport.testing import INTEGRATION
from collective.dms.batchimport.utils import createDocument
from datetime import datetime
from plone import api
from plone.app.testing import login
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME
from plone.namedfile.file import NamedBlobFile
from zope.interface import Invalid

import unittest


class TestUtils(unittest.TestCase):

    layer = INTEGRATION

    def setUp(self):
        self.app = self.layer["app"]
        self.portal = self.layer["portal"]
        self.request = self.layer["request"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        login(self.portal, TEST_USER_NAME)
        self.folder = api.content.create(
            container=self.portal, type="Folder", id="folder"
        )

    def test_createDocument(self):
        file_object = NamedBlobFile(data=b"data", filename="data.txt")
        document, version = createDocument(
            self.portal,
            self.folder,
            "dmsdocument",
            "My doc",
            file_object,
            owner=TEST_USER_NAME,
        )
        self.assertIn(version.id, document.objectIds())

        document, version = createDocument(
            self.portal,
            self.folder,
            "dmsincomingmail",
            "My doc",
            file_object,
            owner=TEST_USER_NAME,
            metadata={"internal_reference_no": "12345"},
        )
        with self.assertRaises(Invalid):
            document, version = createDocument(
                self.portal,
                self.folder,
                "dmsincomingmail",
                "My doc",
                file_object,
                owner=TEST_USER_NAME,
                metadata={"internal_reference_no": "12345"},
            )

        document, version = createDocument(
            self.portal,
            self.folder,
            "dmsincomingmail",
            "My mail",
            file_object,
            owner=TEST_USER_NAME,
            metadata=None,
        )
        self.assertTrue(isinstance(document.reception_date, datetime))
        self.assertEqual(document.internal_reference_no, "in/2")

        document, version = createDocument(
            self.portal,
            self.folder,
            "dmsoutgoingmail",
            "My sent mail",
            file_object,
            owner=TEST_USER_NAME,
            metadata=None,
        )
        self.assertEqual(version.title, "Scanned Mail")

        document, version = createDocument(
            self.portal,
            self.folder,
            "dmsoutgoingmail",
            "My sent mail",
            file_object,
            owner=TEST_USER_NAME,
            metadata={"file_title": "My title"},
        )
        self.assertEqual(version.title, "My title")
