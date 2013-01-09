from zope.interface import Interface
from zope import schema

from Products.Five.browser import BrowserView

from plone.autoform.directives import widget
from collective.z3cform.datagridfield import DataGridFieldFactory
from collective.z3cform.datagridfield.registry import DictRow

from plone.app.registry.browser import controlpanel


from . import _

class ICodeTypeMapSchema(Interface):
    code = schema.TextLine(title=_("Code"))
    portal_type = schema.TextLine(title=_("Portal Type"))

class ISettings(Interface):
    fs_root_directory = schema.TextLine(
        title=_("FS Root Directory"))

    code_to_type_mapping = schema.List(
        title=_("Code to Portal Type Mapping"),
        value_type=DictRow(title=_("Mapping"),
                           schema=ICodeTypeMapSchema)
        )
    widget(code_to_type_mapping=DataGridFieldFactory)

class BatchImporter(BrowserView):
    pass


class ControlPanelEditForm(controlpanel.RegistryEditForm):
    schema = ISettings
    label = _(u'Batch Import Settings')
    description = u''


class ControlPanel(controlpanel.ControlPanelFormWrapper):
    form = ControlPanelEditForm

