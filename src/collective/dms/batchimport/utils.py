import logging
import os

from plone import api
from plone.dexterity.utils import createContentInContainer

from collective.dms.mailcontent.dmsmail import internalReferenceIncomingMailDefaultValue, receptionDateDefaultValue

try:
    from pfwbged.basecontent.behaviors import IDeadline, deadlineDefaultValue
except ImportError:
    IDeadline = None

from . import _

log = logging.getLogger('collective.dms.batchimport')


def createDocument(context, folder, portal_type, document_id, filename,
        file_object, owner=None, metadata=None):
    if owner is None:
        owner = api.user.get_current().id

    if not metadata:
        metadata = {}

    if 'title' in metadata:
        document_title = metadata.get('title')
        del metadata['title']
    else:
        document_title = document_id

    if portal_type == 'dmsincomingmail':
        metadata['internal_reference_no'] = internalReferenceIncomingMailDefaultValue(context)
        metadata['reception_date'] = receptionDateDefaultValue(context)

    log.info('creating the document for real (%s)' % document_title)
    with api.env.adopt_user(username=owner):
        document = createContentInContainer(folder, portal_type,
                title=document_title, **metadata)
        log.info('document has been created (id: %s)' % document.id)

        if IDeadline and IDeadline.providedBy(document):
            document.deadline = deadlineDefaultValue(None)

        version = createContentInContainer(document, 'dmsmainfile',
                title=_('Scanned Mail'),
                file=file_object)
