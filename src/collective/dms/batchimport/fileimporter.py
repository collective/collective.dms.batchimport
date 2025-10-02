from . import _
from . import utils
from plone.autoform.form import AutoExtensibleForm
from plone.i18n.normalizer.interfaces import IIDNormalizer
from plone.namedfile.field import NamedBlobFile
from Products.CMFCore.utils import getToolByName
from z3c.form import form
from zope import schema
from zope.component import queryUtility
from zope.interface import Interface

import logging
import os
import os.path
import z3c.form.button


log = logging.getLogger("collective.dms.batchimport")


class IImportFileFormSchema(Interface):
    file = NamedBlobFile(title=_("File"))

    title = schema.Text(required=False)
    portal_type = schema.Text(required=False)
    location = schema.Text(required=False)
    owner = schema.Text(required=False)


class ImportFileForm(AutoExtensibleForm, form.Form):
    schema = IImportFileFormSchema
    ignoreContext = True

    def get_folder(self, foldername):
        folder = getToolByName(self.context, "portal_url").getPortalObject()
        for part in foldername.split("/"):
            if not part:
                continue
            folder = getattr(folder, part)
        return folder

    def convertTitleToId(self, title):
        """Plug into plone's id-from-title machinery."""
        newid = queryUtility(IIDNormalizer).normalize(title)
        return newid

    @z3c.form.button.buttonAndHandler(_("Import"), name="import")
    def import_file(self, action):
        # Extract form field values and errors from HTTP request
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return

        portal_type = data["portal_type"]
        filename = data["file"].filename
        owner = data["owner"]
        folder = self.get_folder(data["location"])

        document_id = self.convertTitleToId(os.path.splitext(filename)[0])

        utils.createDocument(self, folder, portal_type, document_id, data["file"], owner)
