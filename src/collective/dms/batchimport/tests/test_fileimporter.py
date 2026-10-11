# -*- coding: utf-8 -*-
from AccessControl import Unauthorized
from collective.dms.batchimport.testing import INTEGRATION
from io import BytesIO
from plone import api
from plone.app.testing import login
from plone.app.testing import logout
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from zope.component import queryMultiAdapter
from ZPublisher.HTTPRequest import FileUpload

import unittest


class FieldStorage(object):
    """Uploaded file, as the publisher gives it to FileUpload"""

    def __init__(self, data, filename):
        self.file = BytesIO(data)
        self.filename = filename
        self.headers = {}
        self.name = "form.widgets.file"  # Plone 6: read by Zope 5's FileUpload


class TestImportFileForm(unittest.TestCase):

    layer = INTEGRATION

    def setUp(self):
        self.portal = self.layer["portal"]
        self.request = self.layer["request"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        # createDocument adopts the current user by its id: a user whose login is its id, as in iA.Docs
        api.user.create(email="siteadmin@example.com", username="siteadmin", password="SiteAdm!n0", roles=["Manager"])
        api.user.create(email="agent@example.com", username="agent", password="Agent!1234", roles=["Contributor"])
        login(self.portal, "siteadmin")
        self.folder = api.content.create(container=self.portal, type="Folder", id="incoming", title="Incoming")
        api.content.create(container=self.folder, type="Folder", id="2024", title="2024")

    def submit(self, filename=u"Letter.pdf", **fields):
        """Submit the import form with this file and these text fields"""
        values = dict(("form.widgets.%s" % name, value) for name, value in fields.items())
        if filename:
            values["form.widgets.file"] = FileUpload(FieldStorage(b"%PDF-1.4 letter", filename))
        values["form.buttons.import"] = u"Import"
        # request.get reads request.other before request.form: the values of a previous submit stay there
        for data in (self.request.form, self.request.other):
            for key in [key for key in data if key.startswith("form.")]:
                del data[key]
        self.request.form.update(values)
        form = self.portal.restrictedTraverse("@@fileimport")
        form.update()
        return form

    def test_get_folder(self):
        form = self.portal.restrictedTraverse("@@fileimport")
        self.assertEqual(form.get_folder(u""), self.portal)
        self.assertEqual(form.get_folder(u"incoming/2024"), self.folder["2024"])
        self.assertEqual(form.get_folder(u"/incoming/"), self.folder)
        self.assertRaises(AttributeError, form.get_folder, u"archives")

    def test_convertTitleToId(self):
        form = self.portal.restrictedTraverse("@@fileimport")
        self.assertEqual(form.convertTitleToId(u"Letter 9"), "letter-9")
        self.assertEqual(form.convertTitleToId(u"Réponse à l'avis"), "reponse-a-lavis")
        self.assertEqual(form.convertTitleToId("éàâ Ç&%$"), "eaa-c")

    def test_import_file(self):
        # a form of the site root, for managers
        html = self.portal.restrictedTraverse("@@fileimport")()
        for name in ("file", "title", "portal_type", "location", "owner"):
            self.assertIn('name="form.widgets.%s' % name, html)
        self.assertIn('name="form.buttons.import"', html)
        self.assertIsNone(queryMultiAdapter((self.folder, self.request), name="fileimport"))
        login(self.portal, "agent")
        self.assertRaises(Unauthorized, self.portal.restrictedTraverse, "@@fileimport")
        logout()
        self.assertRaises(Unauthorized, self.portal.restrictedTraverse, "@@fileimport")
        login(self.portal, "siteadmin")
        # the file is required
        form = self.submit(filename=None, portal_type=u"dmsincomingmail", location=u"incoming")
        self.assertEqual(form.status, form.formErrorsMessage)
        self.assertEqual(self.folder.objectIds(), ["2024"])
        # Plone 4: the owner field is given as main file type (Known issues), the title field is not used
        form = self.submit(
            portal_type=u"dmsincomingmail", location=u"incoming/2024", title=u"Complaint", owner=u"dmsmainfile"
        )
        self.assertEqual(form.status, u"")
        document = self.folder["2024"]["letter"]
        self.assertEqual((document.portal_type, document.title), ("dmsincomingmail", u"letter"))
        self.assertEqual(document.getOwner().getId(), "siteadmin")
        self.assertEqual(document.internal_reference_no, u"in/1")
        self.assertEqual(document.objectIds(), ["scanned-mail"])
        main_file = document["scanned-mail"]
        self.assertEqual(main_file.portal_type, "dmsmainfile")
        self.assertEqual(main_file.file.data, b"%PDF-1.4 letter")
        self.assertEqual(main_file.file.filename, u"Letter.pdf")
        # Plone 4: no location or no owner (no main file type) raise errors (Known issues)
        self.assertRaises(
            AttributeError, self.submit, filename=u"Note.pdf", portal_type=u"dmsdocument", owner=u"dmsmainfile"
        )
        # Plone 6: ValueError (main file type None) instead of ComponentLookupError
        self.assertRaises(
            ValueError, self.submit, filename=u"Note.pdf", portal_type=u"dmsdocument", location=u"incoming"
        )

    @unittest.expectedFailure
    def test_import_file_owner(self):
        """The owner field is passed as main file type to createDocument (Known issues)"""
        self.submit(portal_type=u"dmsincomingmail", location=u"incoming", owner=u"agent")
        document = self.folder["letter"]
        self.assertEqual(document.getOwner().getId(), "agent")
        self.assertEqual(document["scanned-mail"].portal_type, "dmsmainfile")

    @unittest.expectedFailure
    def test_import_file_location(self):
        """No location is the site root, as for the batch import: AttributeError on Plone 4 (Known issues)"""
        self.submit(portal_type=u"dmsdocument", owner=u"dmsmainfile")
        self.assertEqual(self.portal["letter"].portal_type, "dmsdocument")

    @unittest.expectedFailure
    def test_import_file_title(self):
        """The title field is not used: the document title is its id (Known issues)"""
        self.submit(portal_type=u"dmsincomingmail", location=u"incoming", title=u"Complaint", owner=u"dmsmainfile")
        self.assertEqual(self.folder["letter"].title, u"Complaint")
