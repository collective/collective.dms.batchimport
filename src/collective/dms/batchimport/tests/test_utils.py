# -*- coding: utf-8 -*-
from collective.dms.batchimport.testing import INTEGRATION
from collective.dms.batchimport.utils import createDocument
from datetime import datetime
from plone import api
from plone.app.testing import login
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME
from plone.namedfile.file import NamedBlobFile
from zope.component import getMultiAdapter
from zope.interface import Invalid

import unittest


class TestUtils(unittest.TestCase):

    layer = INTEGRATION

    def setUp(self):
        self.portal = self.layer["portal"]
        self.request = self.layer["request"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        login(self.portal, TEST_USER_NAME)
        self.folder = api.content.create(container=self.portal, type="Folder", id="incoming", title="Incoming")
        # users whose login is their id, as in iA.Docs: the scanner account, an agent
        api.user.create(email="scanner@example.com", username="scanner", password="Scanner!12", roles=["Manager"])
        api.user.create(email="agent@example.com", username="agent", password="Agent!1234", roles=["Contributor"])
        # imio.zamqp.dms passes an object with context and request, used by the internal reference defaults
        self.context = getMultiAdapter((self.portal, self.request), name="batchimport")

    def test_createDocument(self):
        login(self.portal, "scanner")
        scan = NamedBlobFile(data=b"%PDF-1.4 letter", filename=u"letter.pdf")
        # incoming mail: owned by the current user, default internal reference and reception date
        document, main_file = createDocument(self.context, self.folder, "dmsincomingmail", u"Letter", scan)
        self.assertEqual(document.aq_parent, self.folder)
        self.assertEqual((document.id, document.portal_type, document.title), ("letter", "dmsincomingmail", u"Letter"))
        self.assertEqual(document.getOwner().getId(), "scanner")
        self.assertEqual(document.Creator(), "scanner")
        self.assertEqual(document.internal_reference_no, u"in/1")
        self.assertIsInstance(document.reception_date, datetime)
        self.assertEqual(document.objectIds(), ["scanned-mail"])
        self.assertEqual(main_file, document["scanned-mail"])
        self.assertEqual(main_file.portal_type, "dmsmainfile")
        self.assertEqual(main_file.title, u"Scanned Mail")
        self.assertEqual(main_file.file, scan)
        self.assertEqual(main_file.getOwner().getId(), "scanner")
        # owner: created as this user, whatever the current user
        document, main_file = createDocument(
            self.context, self.folder, "dmsincomingmail", u"Claim", scan, owner="agent"
        )
        self.assertEqual(document.getOwner().getId(), "agent")
        self.assertEqual(document.Creator(), "agent")
        self.assertEqual(main_file.Creator(), "agent")
        self.assertEqual(document.internal_reference_no, u"in/2")
        # metadata: document fields (title included), file_title is the main file title
        document, main_file = createDocument(
            self.context,
            self.folder,
            "dmsincomingmail",
            u"ignored",
            scan,
            metadata={
                "title": u"Invoice",
                "internal_reference_no": u"IN-2024-7",
                "reception_date": datetime(2024, 3, 1, 9, 30),
                "file_title": u"Original scan",
            },
        )
        self.assertEqual((document.id, document.title), ("invoice", u"Invoice"))
        self.assertEqual(document.internal_reference_no, u"IN-2024-7")
        self.assertEqual(document.reception_date, datetime(2024, 3, 1, 9, 30))
        self.assertEqual(main_file.title, u"Original scan")
        self.assertFalse(hasattr(document, "file_title"))
        # an existing internal reference number of the same type is refused
        with self.assertRaises(Invalid) as cm:
            metadata = {"internal_reference_no": u"in/1"}
            createDocument(self.context, self.folder, "dmsincomingmail", u"Again", scan, metadata=metadata)
        self.assertEqual(
            cm.exception.args[0], u"Internal reference number (in/1) already exists on type dmsincomingmail"
        )
        self.assertNotIn("again", self.folder.objectIds())
        # outgoing mail: default internal reference, no reception date; same number as an incoming mail
        document, main_file = createDocument(
            self.context,
            self.folder,
            "dmsoutgoingmail",
            u"Answer",
            scan,
            mainfile_type="dmsappendixfile",
            file_metadata={"title": u"Signed answer", "description": u"With signature"},
        )
        self.assertEqual(document.internal_reference_no, u"out/1")
        self.assertFalse(getattr(document, "reception_date", None))
        self.assertEqual(main_file.portal_type, "dmsappendixfile")
        self.assertEqual((main_file.id, main_file.title), ("signed-answer", u"Signed answer"))
        self.assertEqual(main_file.description, u"With signature")
        document, main_file = createDocument(
            self.context, self.folder, "dmsoutgoingmail", u"Reply", scan, metadata={"internal_reference_no": u"in/1"}
        )
        self.assertEqual(document.internal_reference_no, u"in/1")
        # other types: no internal reference number
        document, main_file = createDocument(self.context, self.folder, "dmsdocument", u"Note", scan)
        self.assertEqual(document.portal_type, "dmsdocument")
        self.assertFalse(getattr(document, "internal_reference_no", None))
        self.assertEqual(main_file.title, u"Scanned Mail")

    def test_createDocument_owner_login(self):
        """The default owner is the current user, whose login differs from its id"""
        # Plone 6: fixed on the branch (getUserName() instead of .id): UserNotFoundError on Plone 4 (Known issues)
        scan = NamedBlobFile(data=b"%PDF-1.4 letter", filename=u"letter.pdf")
        document, main_file = createDocument(self.context, self.folder, "dmsdocument", u"Note", scan)
        self.assertEqual(document.getOwner().getId(), TEST_USER_ID)
