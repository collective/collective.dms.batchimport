from collective.dms.mailcontent.dmsmail import internalReferenceIncomingMailDefaultValue
from collective.dms.mailcontent.dmsmail import internalReferenceOutgoingMailDefaultValue
from collective.dms.mailcontent.dmsmail import receptionDateDefaultValue
from imio.helpers.content import find
from plone import api
from plone.dexterity.utils import createContentInContainer

import logging


try:
    from pfwbged.basecontent.behaviors import deadlineDefaultValue
    from pfwbged.basecontent.behaviors import IDeadline
except ImportError:
    IDeadline = None

from . import _


log = logging.getLogger("collective.dms.batchimport")


def createDocument(
    context, folder, portal_type, title, file_object, mainfile_type="dmsmainfile", owner=None, metadata=None
):
    if owner is None:
        owner = api.user.get_current().id

    if not metadata:
        metadata = {}

    if "title" not in metadata and title:
        metadata["title"] = title

    if portal_type.startswith("dmsincoming"):
        if "internal_reference_no" not in metadata:
            metadata["internal_reference_no"] = internalReferenceIncomingMailDefaultValue(context)
        if "reception_date" not in metadata:
            metadata["reception_date"] = receptionDateDefaultValue(context)
    elif portal_type.startswith("dmsoutgoing"):
        if "internal_reference_no" not in metadata:
            metadata["internal_reference_no"] = internalReferenceOutgoingMailDefaultValue(context)
    if "internal_reference_no" in metadata:
        if find(
            unrestricted=True, portal_type=portal_type, internal_reference_number=metadata["internal_reference_no"]
        ):
            raise ValueError(
                _(
                    "Internal reference number (${irn}) already exists on type ${type}",
                    mapping={"irn": metadata["internal_reference_no"], "type": portal_type},
                )
            )

    file_title = _("Scanned Mail")
    if "file_title" in metadata:
        file_title = metadata["file_title"]
        del metadata["file_title"]

    with api.env.adopt_user(username=owner):
        document = createContentInContainer(folder, portal_type, **metadata)
        log.info("document has been created (id: %s)" % document.id)

        if IDeadline and IDeadline.providedBy(document):
            document.deadline = deadlineDefaultValue(None)

        version = createContentInContainer(document, mainfile_type, title=file_title, file=file_object)
        log.info("file document has been created (id: %s)" % version.id)
        return (document, version)
