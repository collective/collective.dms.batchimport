from collective.dms.batchimport.testing import INTEGRATION
from plone.base.utils import get_installer

import unittest


class TestSetup(unittest.TestCase):

    layer = INTEGRATION

    def setUp(self):
        self.app = self.layer["app"]
        self.portal = self.layer["portal"]
        self.request = self.layer["request"]
        self.installer = get_installer(self.portal, self.request)

    def test_install(self):
        self.assertTrue(self.installer.is_product_installed("collective.dms.batchimport"))

    def test_uninstall(self):
        self.installer.uninstall_product("collective.dms.batchimport")
        self.assertFalse(self.installer.is_product_installed("collective.dms.batchimport"))
