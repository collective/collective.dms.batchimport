import os
import logging
import json

from zope.interface import Interface
from zope import schema
from zope import component
from zope.component import queryUtility

from Products.CMFCore.utils import getToolByName
from Products.Five.browser import BrowserView

from plone.autoform.directives import widget
from plone.namedfile.file import NamedBlobFile
from plone.registry.interfaces import IRegistry
from plone.i18n.normalizer.interfaces import IIDNormalizer
from collective.z3cform.datagridfield import DataGridFieldFactory
from collective.z3cform.datagridfield.registry import DictRow
from plone.app.registry.browser import controlpanel

from . import _
from . import utils

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

        excluded_dirs = []
        for basename, dirnames, filenames in os.walk(self.fs_root_directory):
            # avoid folders beginning with .
            if os.path.basename(basename).startswith('.'):
                excluded_dirs.append("%s/" % basename)
                continue
            if any(basename.startswith(s) for s in excluded_dirs):
                continue
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
                    log.warning('error importing %s (%s)' %
                                (os.path.join(foldername, filename), str(e)))
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
                    log.warning('error importing %s (%s)' %
                                (os.path.join(foldername, filename), str(e)))
                    nb_errors += 1
                else:
                    self.mark_as_processed(filepath)
                    nb_imports += 1

        return 'OK (%s imported files, %s unprocessed files)' % (nb_imports, nb_errors)

    def mark_as_processed(self, filepath):
        # if the processed folder is the same as the input folder, we dont move files
        if self.processed_fs_root_directory == self.fs_root_directory:
            return
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

    def convertTitleToId(self, title):
        """Plug into plone's id-from-title machinery.
        """
        #title = title.decode('utf-8')
        newid = queryUtility(IIDNormalizer).normalize(title)
        return newid

    def import_one(self, filepath, foldername, metadata=None):
        filename = os.path.basename(filepath)
        try:
            folder = self.get_folder(foldername)
        except AttributeError:
            raise BatchImportError('directory structure mismatch')
        code = filename.split('-', 1)[0]
        portal_type = self.code_to_type_mapping.get(code)
        if not portal_type:
            raise BatchImportError("no portal type associated to this code '%s'" % code)

        document_id = self.convertTitleToId(os.path.splitext(filename)[0])

        if hasattr(folder, document_id):
            raise BatchImportError('document already exists')

        document_file = NamedBlobFile(file(filepath).read(), filename=unicode(filename))
        utils.createDocument(self, folder, portal_type, document_id,
                             document_file, metadata=metadata)


class ControlPanelEditForm(controlpanel.RegistryEditForm):
    schema = ISettings
    label = _(u'Batch Import Settings')
    description = u''


class ControlPanel(controlpanel.ControlPanelFormWrapper):
    form = ControlPanelEditForm
