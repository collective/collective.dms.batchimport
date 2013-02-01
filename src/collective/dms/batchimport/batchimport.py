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


class BatchImportError(Exception):
    pass


class ICodeTypeMapSchema(Interface):
    code = schema.TextLine(title=_("Code"))
    portal_type = schema.TextLine(title=_("Portal Type"))


class ISettings(Interface):
    fs_root_directory = schema.TextLine(
        title=_("FS Root Directory"))

    processed_fs_root_directory = schema.TextLine(
        title=_("FS Root Directory for processed files"))

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
            return 'ERROR'

        if not os.path.exists(settings.fs_root_directory):
            log.warning('settings.fs_root_directory do not exist')
            return 'ERROR'

        self.fs_root_directory = settings.fs_root_directory
        if not self.fs_root_directory.endswith('/'):
            self.fs_root_directory = self.fs_root_directory + '/'

        self.processed_fs_root_directory = settings.processed_fs_root_directory
        if not self.processed_fs_root_directory.endswith('/'):
            self.processed_fs_root_directory = self.processed_fs_root_directory + '/'

        self.code_to_type_mapping = dict()
        for mapping in settings.code_to_type_mapping:
            self.code_to_type_mapping[mapping['code']] = mapping['portal_type']

        nb_imports = 0
        nb_errors = 0

        for basename, dirnames, filenames in os.walk(self.fs_root_directory):
            # avoid folders beginning with .
            if os.path.basename(basename).startswith('.'): continue
            metadata_filenames = [x for x in filenames if x.endswith('.metadata')]
            other_filenames = [x for x in filenames if not x.endswith('.metadata') and not x.startswith('.')]

            # first pass, handle metadata files
            for filename in metadata_filenames:
                metadata_filepath = os.path.join(basename, filename)
                foldername = basename[len(self.fs_root_directory):]

                metadata = json.load(file(metadata_filepath))

                imported_filename = os.path.splitext(filename)[0]
                filepath = os.path.join(basename, imported_filename)

                try:
                    self.import_one(filepath, foldername, metadata)
                except BatchImportError as e:
                    log.warning(str(e))
                    nb_errors += 1
                else:
                    self.mark_as_processed(metadata_filepath)
                    self.mark_as_processed(filepath)
                    nb_imports += 1

                other_filenames.remove(imported_filename)

            # second pass, handle other files, creating individual documents
            for filename in other_filenames:
                filepath = os.path.join(basename, filename)
                foldername = basename[len(self.fs_root_directory):]
                try:
                    self.import_one(filepath, foldername)
                except BatchImportError as e:
                    log.warning(str(e))
                    nb_errors += 1
                else:
                    self.mark_as_processed(filepath)
                    nb_imports += 1

        return 'OK (%s imported files, %s unprocessed files)' % (nb_imports, nb_errors)

    def mark_as_processed(self, filepath):
        processed_filepath = os.path.join(self.processed_fs_root_directory,
                        filepath[len(self.fs_root_directory):])
        if not os.path.exists(os.path.dirname(processed_filepath)):
            os.makedirs(os.path.dirname(processed_filepath))
        os.rename(filepath, processed_filepath)

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
            raise BatchImportError("filesystem directory '%s' doesn't match a plone folder"%foldername)
        code = filename.split('-', 1)[0]
        portal_type = self.code_to_type_mapping.get(code)
        if not portal_type:
            raise BatchImportError("no portal type associated to this code '%s'"%code)

        document_id = os.path.splitext(filename)[0]

        if hasattr(folder, document_id):
            raise BatchImportError('document already exists')

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

