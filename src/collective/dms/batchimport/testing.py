# -*- coding: utf8 -*-
from collective.dms.basecontent.source import CategoryVocabulary
from collective.dms.batchimport import _
from collective.dms.batchimport.batchimport import ICodeTypeMapSchema
from collective.dms.batchimport.batchimport import ISettings
from collective.z3cform.datagridfield.registry import DictRow
from plone import api
from plone.app.robotframework.content import Content
from plone.app.robotframework.remote import RemoteLibraryLayer
from plone.app.robotframework.testing import REMOTE_LIBRARY_BUNDLE_FIXTURE
from plone.app.robotframework.utils import disableCSRFProtection
from plone.app.testing import applyProfile
from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import PloneSandboxLayer
from plone.app.testing import setRoles
from plone.testing.zope import WSGI_SERVER_FIXTURE
from zope.globalrequest.local import setLocal

import collective.dms.batchimport
import transaction


class DmsBatchimportLayer(PloneSandboxLayer):

    defaultBases = (PLONE_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        self.loadZCML(package=collective.dms.batchimport, name="testing.zcml")

    def setUpPloneSite(self, portal):
        setLocal("request", portal.REQUEST)  # collective.fingerpointing subscribers need a request
        applyProfile(portal, "collective.dms.batchimport:default")
        # creating a dmsmainfile (an iconifiedcategory annex) needs a categories config, as in iA.Docs
        with api.env.adopt_roles(["Manager"]):
            CategoryVocabulary().create_default_category()
        transaction.commit()
        setLocal("request", None)


COLLECTIVE_DMS_BATCHIMPORT = DmsBatchimportLayer(name="COLLECTIVE_DMS_BATCHIMPORT")

INTEGRATION = IntegrationTesting(bases=(COLLECTIVE_DMS_BATCHIMPORT,), name="INTEGRATION")

FUNCTIONAL = FunctionalTesting(bases=(COLLECTIVE_DMS_BATCHIMPORT,), name="FUNCTIONAL")


class DmsBatchimportAcceptanceLayer(PloneSandboxLayer):
    """Robot data: a manager (the control panel needs Manage portal), a batch importer (Contributor too: the
    documents are created as the current user), a plain member, an "incoming" folder"""

    defaultBases = (COLLECTIVE_DMS_BATCHIMPORT,)

    def setUpPloneSite(self, portal):
        # the DictRow of the settings schema was stored with the registry records by the base layer, whose
        # connection is closed now (ConnectionStateError when the control panel is rendered): a fresh one
        ISettings["code_to_type_mapping"].value_type = DictRow(title=_("Mapping"), schema=ICodeTypeMapSchema)
        setLocal("request", portal.REQUEST)
        api.user.create(email="manager@example.com", username="manager", password="Manager!12")
        api.user.create(email="importer@example.com", username="importer", password="Import!123")
        api.user.create(email="member@example.com", username="member", password="Member!123")
        # api.user.create(roles=…) refuses roles the current user (none here) hasn't got
        setRoles(portal, "manager", ["Member", "Manager"])
        setRoles(portal, "importer", ["Member", "Batch importer", "Contributor"])
        with api.env.adopt_roles(["Manager"]):
            api.content.create(container=portal, type="Folder", id="incoming", title="Incoming")
        transaction.commit()
        setLocal("request", None)


ACCEPTANCE_FIXTURE = DmsBatchimportAcceptanceLayer(name="ACCEPTANCE_FIXTURE")


class CSRFSafeContent(Content):
    """Set field value is aborted by plone.protect on Plone 6 otherwise (Create content disables the check)"""

    def set_field_value(self, uid, field, value, field_type):
        disableCSRFProtection()
        return super(CSRFSafeContent, self).set_field_value(uid, field, value, field_type)


REMOTE_LIBRARY_FIXTURE = RemoteLibraryLayer(
    bases=(PLONE_FIXTURE,),
    libraries=tuple(
        CSRFSafeContent if lib is Content else lib for lib in REMOTE_LIBRARY_BUNDLE_FIXTURE.libraryBases[1:]
    ),
    name="RemoteLibraryBundle:RobotRemote",
)

ACCEPTANCE = FunctionalTesting(
    bases=(ACCEPTANCE_FIXTURE, REMOTE_LIBRARY_FIXTURE, WSGI_SERVER_FIXTURE), name="ACCEPTANCE"
)
