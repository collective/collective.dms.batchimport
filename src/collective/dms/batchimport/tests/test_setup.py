# -*- coding: utf-8 -*-
from AccessControl import Unauthorized
from collective.dms.batchimport import _
from collective.dms.batchimport.testing import INTEGRATION
from plone import api
from plone.app.testing import login
from plone.app.testing import logout
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.base.utils import get_installer
from plone.registry.interfaces import IRegistry
from zope.component import getUtility
from zope.component import queryMultiAdapter
from zope.i18n import translate

import unittest


class TestSetup(unittest.TestCase):
    """configure.zcml and the default profile"""

    layer = INTEGRATION

    def setUp(self):
        self.app = self.layer["app"]
        self.portal = self.layer["portal"]
        self.request = self.layer["request"]
        self.installer = get_installer(self.portal, self.request)  # Plone 6: no portal_quickinstaller
        setRoles(self.portal, TEST_USER_ID, ["Manager"])

    def test_product_is_installed(self):
        """Validate that our products GS profile has been run and the product
        installed
        """
        self.assertTrue(self.installer.is_product_installed("collective.dms.batchimport"))

    def test_uninstall(self):
        # Plone 6: uninstall profile (branch)
        self.installer.uninstall_product("collective.dms.batchimport")
        self.assertFalse(self.installer.is_product_installed("collective.dms.batchimport"))
        actions = self.portal.portal_controlpanel.listActions()
        self.assertNotIn("collective.dms.batchimport", [action.id for action in actions])
        self.assertNotIn("collective.dms.batchimport.batchimport.ISettings.fs_root_directory", getUtility(IRegistry))

    def test_metadata(self):
        setup = self.portal.portal_setup
        self.assertEqual(setup.getLastVersionForProfile("collective.dms.batchimport:default"), ("0001",))
        self.assertNotEqual(setup.getLastVersionForProfile("collective.dms.mailcontent:default"), "unknown")
        self.assertIn("dmsincomingmail", self.portal.portal_types.objectIds())

    def test_registry(self):
        registry = getUtility(IRegistry)
        prefix = "collective.dms.batchimport.batchimport.ISettings."
        for name in ("fs_root_directory", "processed_fs_root_directory", "code_to_type_mapping"):
            self.assertIn(prefix + name, registry.records)
            self.assertIsNone(registry[prefix + name])

    def test_controlpanel(self):
        actions = self.portal.portal_controlpanel.listActions()
        configlets = [action for action in actions if action.id == "collective.dms.batchimport"]
        self.assertEqual(len(configlets), 1)
        configlet = configlets[0]
        self.assertEqual(configlet.title, "Batch Import")
        self.assertEqual(configlet.category, "Products")
        self.assertEqual(configlet.appId, "collective.dms.batchimport")
        # not the "Manage portal" permission (Known issues): Manager only, as Manage portal
        self.assertEqual(configlet.permissions, ("Manage Portal",))
        self.assertTrue(configlet.visible)
        self.assertEqual(configlet.getActionExpression(), "string:${portal_url}/@@batchimport-controlpanel")
        # Plone 6: Bootstrap icon name
        self.assertEqual(configlet.getIconExpression(), "string:box-arrow-in-up")

    def test_rolemap(self):
        self.assertIn("Batch importer", self.portal.validRoles())
        permission = "collective.dms.batchimport: Batch import"
        roles = [role["name"] for role in self.portal.rolesOfPermission(permission) if role["selected"]]
        self.assertEqual(roles, ["Batch importer", "Manager", "Site Administrator"])
        self.assertTrue(self.portal.acquiredRolesAreUsedBy(permission))

    def test_configure(self):
        # @@batchimport: site root, Batch import permission; @@batchimport-controlpanel: site root, Manage portal
        api.content.create(container=self.portal, type="Folder", id="incoming")
        for name in ("batchimport", "batchimport-controlpanel"):
            self.assertIsNotNone(queryMultiAdapter((self.portal, self.request), name=name))
            self.assertIsNone(queryMultiAdapter((self.portal["incoming"], self.request), name=name))
        api.user.create(email="importer@example.com", username="importer", password="Import!123")
        api.user.grant_roles(username="importer", roles=["Batch importer"])
        api.user.create(email="siteadmin@example.com", username="siteadmin", password="SiteAdm!n0")
        api.user.grant_roles(username="siteadmin", roles=["Site Administrator"])
        api.user.create(email="member@example.com", username="member", password="Member!123")
        self.portal.restrictedTraverse("@@batchimport")
        self.portal.restrictedTraverse("@@batchimport-controlpanel")
        # Manage portal is given to Manager only
        login(self.portal, "siteadmin")
        self.portal.restrictedTraverse("@@batchimport")
        self.assertRaises(Unauthorized, self.portal.restrictedTraverse, "@@batchimport-controlpanel")
        login(self.portal, "importer")
        self.portal.restrictedTraverse("@@batchimport")
        self.assertRaises(Unauthorized, self.portal.restrictedTraverse, "@@batchimport-controlpanel")
        login(self.portal, "member")
        self.assertRaises(Unauthorized, self.portal.restrictedTraverse, "@@batchimport")
        logout()
        self.assertRaises(Unauthorized, self.portal.restrictedTraverse, "@@batchimport")


class TestTranslations(unittest.TestCase):
    """French translations of locales (registered in configure.zcml)"""

    layer = INTEGRATION

    def fr(self, msgid, **mapping):
        return translate(_(msgid, mapping=mapping), target_language="fr")

    def test_translations(self):
        self.assertEqual(self.fr("Batch Import"), "Importation batch DMS")
        self.assertEqual(self.fr("Batch Import Settings"), "Configuration de l'importation batch DMS")
        self.assertEqual(self.fr("Code to Portal Type Mapping"), "Correspondance code/type de contenu")
        self.assertEqual(self.fr("FS Root Directory"), "Dossier racine d'import")
        self.assertEqual(self.fr("FS Root Directory for processed files"), "Dossier racine pour les fichiers traités")
        self.assertEqual(self.fr("Scanned Mail"), "Document scanné")
        self.assertEqual(
            self.fr(
                "Internal reference number (${irn}) already exists on type ${type}",
                irn="in/1",
                type="dmsincomingmail",
            ),
            "Le numero de reference interne (in/1) existe deja pour le type dmsincomingmail",
        )
        # role title, in the plone domain
        self.assertEqual(translate("Batch importer", domain="plone", target_language="fr"), "Importateur en lot")
