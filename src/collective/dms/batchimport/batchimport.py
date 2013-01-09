import os
import logging
import json

from zope.interface import Interface
from zope import schema
from zope import component

from Products.CMFCore.utils import getToolByName
from Products.Five.browser import BrowserView

from plone.autoform.directives import widget
from plone.namedfile.file import NamedBlobFile
from plone.registry.interfaces import IRegistry
from collective.z3cform.datagridfield import DataGridFieldFactory
from collective.z3cform.datagridfield.registry import DictRow

from plone.app.registry.browser import controlpanel


from . import _

log = logging.getLogger('collective.dms.batchimport')


class ICodeTypeMapSchema(Interface):
    code = schema.TextLine(title=_("Code"))
    portal_type = schema.TextLine(title=_("Portal Type"))


class ISettings(Interface):
    fs_root_directory = schema.TextLine(
        title=_("FS Root Directory"))

    code_to_type_mapping = schema.List(
        title=_("Code to Portal Type Mapping"),
        value_type=DictRow(title=_("Mapping"),
                           schema=ICodeTypeMapSchema)
        )
    widget(code_to_type_mapping=DataGridFieldFactory)


class BatchImporter(BrowserView):
    def __call__(self):
        settings = component.getUtility(IRegistry).forInterface(ISettings, False)

        if not settings.fs_root_directory:
            log.warning('settings.fs_root_directory is not defined')
            return

        if not os.path.exists(settings.fs_root_directory):
            log.warning('settings.fs_root_directory do not exist')
            return

        self.code_to_type_mapping = dict()
        for mapping in settings.code_to_type_mapping:
            self.code_to_type_mapping[mapping['code']] = mapping['portal_type']

        for basename, dirnames, filenames in os.walk(settings.fs_root_directory):
            # first pass, handle metadata files (TODO)
            metadata_filenames = [x for x in filenames if x.endswith('.metadata')]
            other_filenames = [x for x in filenames if not x.endswith('.metadata')]

            for filename in metadata_filenames:
                filepath = os.path.join(basename, filename)
                foldername = basename[len(settings.fs_root_directory):]

                metadata = json.load(file(filepath))

                imported_filename = os.path.splitext(filename)[0]
                filepath = os.path.join(basename, imported_filename)

                self.import_one(filepath, foldername, metadata)
                other_filenames.remove(imported_filename)

            # second pass, handle other files, creating individual documents
            for filename in other_filenames:
                filepath = os.path.join(basename, filename)
                foldername = basename[len(settings.fs_root_directory):]
                self.import_one(filepath, foldername)

        # TODO: return the number of files that have been successfully imported.
        return 'OK'

    def get_folder(self, foldername):
        folder = getToolByName(self.context, 'portal_url').getPortalObject()
        for part in foldername.split('/'):
            if not part:
                continue
            folder = getattr(folder, part)
        return folder

    def import_one(self, filepath, foldername, metadata=None):
        filename = os.path.basename(filepath)
        try:
            folder = self.get_folder(foldername)
        except AttributeError:
            log.warning("the directory on the filesystem doesn't match a plone folder")
            return
        code = filename.split('-', 1)[0]
        portal_type = self.code_to_type_mapping.get(code)
        if not portal_type:
            log.warning("no portal type associated to this code")
            return

        document_id = os.path.splitext(filename)[0]

        if hasattr(folder, document_id):
            log.warning("document already exists")
            return

        if not metadata:
            metadata = {}

        if 'title' in metadata:
            document_title = metadata.get('title')
            del metadata['title']
        else:
            document_title = os.path.splitext(filename)[0].split('-', 1)[1]

        log.info("creating the document for real (%s)" % document_id)
        folder.invokeFactory(portal_type, id=document_id, title=document_title,
                        **metadata)

        document = folder[document_id]

        document_file = NamedBlobFile(file(filepath).read(), filename=unicode(filename))
        document.invokeFactory('dmsmainfile', id='main', title=_(u'Main File'),
                        file=document_file)


class ControlPanelEditForm(controlpanel.RegistryEditForm):
    schema = ISettings
    label = _(u'Batch Import Settings')
    description = u''


class ControlPanel(controlpanel.ControlPanelFormWrapper):
    form = ControlPanelEditForm

