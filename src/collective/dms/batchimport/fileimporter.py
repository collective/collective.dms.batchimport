import logging
import os
import os.path

from zope import schema
from plone.dexterity.utils import createContentInContainer

from zope.component import queryUtility
from five import grok
from Products.CMFPlone.interfaces import IPloneSiteRoot
from Products.CMFCore.utils import getToolByName

import z3c.form.button
from plone import api
from plone.directives import form
from plone.i18n.normalizer.interfaces import IIDNormalizer

from collective.dms.mailcontent.dmsmail import internalReferenceIncomingMailDefaultValue, receptionDateDefaultValue

from plone.namedfile.field import NamedFile, NamedBlobFile

from . import _

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

        metadata = {}
        document_id = self.convertTitleToId(os.path.splitext(filename)[0])
        if data.get('title'):
            document_title = data.get('title')
        else:
            document_title = document_id

        if portal_type == 'dmsincomingmail':
            metadata['internal_reference_no'] = internalReferenceIncomingMailDefaultValue(self)
            metadata['reception_date'] = receptionDateDefaultValue(self)

        log.info('creating the document for real (%s)' % document_title)
        with api.env.adopt_user(username=owner):
            document = createContentInContainer(folder, portal_type,
                    title=document_title, **metadata)
            log.info('document has been created (id: %s)' % document.id)

            version = createContentInContainer(document, 'dmsmainfile',
                    title=_('Scanned Mail'),
                    file=data['file'])
