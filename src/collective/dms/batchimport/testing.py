# -*- coding: utf8 -*-
from collective.dms.basecontent.source import CategoryVocabulary
from plone import api
from plone.app.testing import applyProfile
from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import PloneSandboxLayer
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
