# -*- coding: utf8 -*-

from plone.app.testing import PloneWithPackageLayer
from plone.app.testing import IntegrationTesting
from plone.app.testing import FunctionalTesting

import collective.dms.batchimport


class DmsBatchimportLayer(PloneWithPackageLayer):

    def setUpPloneSite(self, portal):
        self.applyProfile(portal, 'collective.dms.batchimport:testing')


COLLECTIVE_DMS_BATCHIMPORT = DmsBatchimportLayer(
    zcml_package=collective.dms.batchimport,
    zcml_filename='testing.zcml',
    gs_profile_id='collective.dms.batchimport:testing',
    name="COLLECTIVE_DMS_BATCHIMPORT")

INTEGRATION = IntegrationTesting(
    bases=(COLLECTIVE_DMS_BATCHIMPORT, ),
    name="INTEGRATION")

FUNCTIONAL = FunctionalTesting(
    bases=(COLLECTIVE_DMS_BATCHIMPORT, ),
    name="FUNCTIONAL")
