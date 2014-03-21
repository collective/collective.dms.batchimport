import logging
import os
import os.path

from zope import schema

from zope.component import queryUtility
from five import grok
from Products.CMFPlone.interfaces import IPloneSiteRoot
from Products.CMFCore.utils import getToolByName

import z3c.form.button
from plone import api
from plone.directives import form
from plone.i18n.normalizer.interfaces import IIDNormalizer

from plone.namedfile.field import NamedFile, NamedBlobFile

from . import _
from . import utils

log = logging.getLogger('collective.dms.batchimport')

class IImportFileFormSchema(form.Schema):
    file = NamedBlobFile(title=_(u"File"))

    title = schema.Text(required=False)
    portal_type = schema.Text(required=False)
    location = schema.Text(required=False)
    owner = schema.Text(required=False)


class ImportFileForm(form.SchemaForm):
    schema = IImportFileFormSchema

    # Permission required to
    grok.require("cmf.ManagePortal")

    ignoreContext = True

    grok.context(IPloneSiteRoot)

    # appear as @@fileimport view
    grok.name("fileimport")

    def get_folder(self, foldername):
        folder = getToolByName(self.context, 'portal_url').getPortalObject()
        for part in foldername.split('/'):
            if not part:
                continue
            folder = getattr(folder, part)
        return folder

    def convertTitleToId(self, title):
        """Plug into plone's id-from-title machinery.
        """
        #title = title.decode('utf-8')
        newid = queryUtility(IIDNormalizer).normalize(title)
        return newid

    @z3c.form.button.buttonAndHandler(_('Import'), name='import')
    def import_file(self, action):
        # Extract form field values and errors from HTTP request
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return

        portal_type = data['portal_type']
        filename = data['file'].filename
        owner = data['owner']
        folder = self.get_folder(data['location'])

        document_id = self.convertTitleToId(os.path.splitext(filename)[0])

        utils.createDocument(self, folder, portal_type, document_id,
                             data['file'], owner)
