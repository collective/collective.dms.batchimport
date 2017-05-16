import logging

from plone import api
from plone.dexterity.utils import createContentInContainer

from collective.dms.mailcontent.dmsmail import (internalReferenceIncomingMailDefaultValue, receptionDateDefaultValue,
                                                internalReferenceOutgoingMailDefaultValue)

try:
    from pfwbged.basecontent.behaviors import IDeadline, deadlineDefaultValue
except ImportError:
    IDeadline = None

from . import _

log = logging.getLogger('collective.dms.batchimport')


def createDocument(context, folder, portal_type, title, file_object, mainfile_type='dmsmainfile', owner=None,
                   metadata=None):
    if owner is None:
        owner = api.user.get_current().id

    if not metadata:
        metadata = {}

    if 'title' not in metadata and title:
        metadata['title'] = title

    if portal_type == 'dmsincomingmail':
        if 'internal_reference_no' not in metadata:
            metadata['internal_reference_no'] = internalReferenceIncomingMailDefaultValue(context)
        if 'reception_date' not in metadata:
            metadata['reception_date'] = receptionDateDefaultValue(context)
    elif portal_type == 'dmsoutgoingmail':
        if 'internal_reference_no' not in metadata:
            metadata['internal_reference_no'] = internalReferenceOutgoingMailDefaultValue(context)

    file_title = _('Scanned Mail')
    if 'file_title' in metadata:
        file_title = metadata['file_title']
        del metadata['file_title']

    with api.env.adopt_user(username=owner):
        document = createContentInContainer(folder, portal_type, **metadata)
        log.info('document has been created (id: %s)' % document.id)

        if IDeadline and IDeadline.providedBy(document):
            document.deadline = deadlineDefaultValue(None)

        version = createContentInContainer(document, mainfile_type, title=file_title,
                                           file=file_object)
        log.info('file document has been created (id: %s)' % version.id)
        return (document, version)
