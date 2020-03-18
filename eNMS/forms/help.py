import os
import re
import posixpath
from pathlib import Path
from flask_wtf import FlaskForm

from wtforms import HiddenField, Label, FieldList
from wtforms.meta import DefaultMeta
from wtforms.form import Form
from wtforms.widgets.core import HTMLString, html_params

from eNMS.setup import settings


class InfiniteDict(dict):
    """
    Internal convenience - see https://stackoverflow.com/questions/48729220/
       set-python-dict-items-recursively-when-given-a-compound-key-foo-bar-baz
    """

    def __missing__(self, val):
        d = InfiniteDict()
        self[val] = d
        return d

    def __getattr__(self, item):
        return self.__getitem__(item)

    def __setattr__(self, item, value):
        super().__setitem__(item, value)


class HelpLabel(Label):
    """
    This class allows for custom rendering of Label information to include the
    Field label and a context-sensitive help icon when help is available.
    """

    def __init__(self, field_id, text, help_url):
        self.field_id = field_id
        self.text = text
        self.help_url = help_url or "/static/help/missing.html"

    def __call__(self, text=None, **kwargs):
        if "for_" in kwargs:
            kwargs["for"] = kwargs.pop("for_")
        else:
            kwargs.setdefault("for", self.field_id)
        kwargs["help_url"] = self.help_url
        attributes = html_params(**kwargs)
        img_attributes = html_params(
            **{
                "for": kwargs["for"],
                "title": f"Help for {self.text}",
                "class": "context-help",
                "help_url": self.help_url,
            }
        )
        return HTMLString(
            "<div><label %s>%s</label>"
            '<img %s data-placement="top" data-toggle="tooltip"'
            'style="margin-left: 6px; padding-bottom: 2px"'
            'src="/static/help/help.svg" width="16"'
            'alt="Click for help"/>'
            "</div>" % (attributes, text or self.text, img_attributes)
        )


class MetaFormHelpRenderer(DefaultMeta):
    """
    This class provides the adjustment to the WTForm behavior to be able to substitute
    our custom HelpLabel for a help-capable field.label.

    Other WTForms extension points seem to typically define an internal 'Meta' class as
    a nested subclass of the Form subclass (i.e., our BaseForm).  We are able to
    avoid this convention by using another Metaclass modify the setup of the 'Meta'
    hierarchy.

    This class also looks for the places (in settings) where help files may be located.
    There is a convention for how these files are named to try to automatically match
    them up to form fields.
    """

    form_name_regexp = re.compile("Form$")
    split_on_capitalization = re.compile("([A-Z]+[^A-Z]+)")
    service_name_regexp = re.compile("_service")

    @staticmethod
    def load_help():
        """
        During initialization for this class, scan the directory structure looking
        for available help files. Relies on some type of standard convention.

        Alternatives: a JSON file could provide this same mapping, but in theory
        this allows addition of new files with zero configuration if the convention
        is tolerable.

        This convention is enough for proof-of-concept, but will need adjustment.
        Today, assuming a directory structure convention that will end in:
        ['service', 'form_name', 'parameter_file.html']

        This is theory also allows for help for more than just forms.

        :return: dictionary
        """
        result = InfiniteDict()  # stackoverflow trick; see above

        def add_help_file(help_path, help_location):
            component_type, component_name, file_name = str(help_path).split(
                os.path.sep
            )[-3:]
            result[component_type][component_name][help_path.stem] = posixpath.join(
                help_location.get("url_path", "/"),
                component_type,
                component_name,
                help_path.name,
            )

        locations = [{"folder": "./eNMS/static/help"}]
        if "help" in settings and "locations" in settings["help"]:
            locations = settings["help"]["locations"]
        for location in locations[::-1]:  # search in reverse order to allow overwrites
            folder = Path("." + location["folder"])
            help_files = list(folder.glob("**/*.html"))
            for help_file in help_files:
                add_help_file(help_file, location)
        return result, len(result.keys()) > 0

    # Static initialization - would love a better alternative than this:
    help_data, help_enabled = load_help.__func__()

    def bind_field(self, form, unbound_field, options=dict()):
        """
        Replace the default behavior - add help label if supported and available
        """
        bound_field = super().bind_field(form, unbound_field, options)
        return self._add_help(form, bound_field, options)

    def wrap_formdata(self, form, formdata):
        return super().wrap_formdata(form, formdata)

    def render_field(self, field, render_kw):
        return super().render_field(field, render_kw)

    def _convert_form_type(self, form_type):
        """Convert 'napalm_ping_service' => 'napalm_ping' """
        return self.service_name_regexp.sub("", form_type).lower()

    def _convert_form_name(self, form_name):
        """Convert 'NapalmPingForm' => 'napalm_ping' """
        return "_".join(
            list(
                filter(
                    lambda x: len(x) > 0 and x != "Form",
                    self.split_on_capitalization.split(form_name),
                )
            )
        ).lower()

    def _has_help(self, form, bound_field):
        """
        Use the form and field to look for any existing context-sensitive help
        If there is no help data, then skip checking.
        """
        if not self.help_enabled or isinstance(bound_field, HiddenField):
            return False
        form_template = getattr(form, "template", "service")
        form_type = getattr(form, "form_type", None)
        if form_type is not None:
            form_type = (
                form.form_type.kwargs["default"]
                if "default" in form.form_type.kwargs.keys()
                else None
            )
        if (
            not form
            or not bound_field
            or form_type is None
            or form_template != "service"
        ):
            return False
        # Note: these are likely to be the same values.
        form_type = self._convert_form_type(form_type)
        # First lookup: based on service (i.e., service/napalm_ping_service/count.html)
        # Skipping: lookup based on class name NapalmPingForm => napalm_ping since this
        # will generally match the first lookup.
        help_file = self.help_data[form_template][form_type][bound_field.name]
        if not help_file:
            # Also look for commonly defined terms/parameters:
            help_file = self.help_data[form_template]["common"][bound_field.name]
        if not help_file:
            # Second lookup: use all potentially relevant superclass forms
            for mro_class in type(form).__mro__:
                if mro_class in [object, FlaskForm, Form, type(form)]:
                    continue
                superclass_name = self._convert_form_name(mro_class.__name__)
                help_file = self.help_data[form_template][superclass_name][
                    bound_field.name
                ]
                if help_file:
                    break
        return help_file

    def _add_help(self, form, bound_field, options):
        """
        Replace the default field.label with an alternate, help-rendering
        HelpLabel instance.
        """
        if not isinstance(bound_field, FieldList):
            help_url = self._has_help(form, bound_field)
            if help_url:
                bound_field.label = HelpLabel(
                    bound_field.id, bound_field.label.text, help_url
                )
        return bound_field
