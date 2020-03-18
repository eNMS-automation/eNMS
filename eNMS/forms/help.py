import os
import re
import posixpath
from pathlib import Path
from flask_wtf import FlaskForm

from wtforms import HiddenField, Label
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
        return HTMLString(
          f"""<div>
            <label {attributes}>{text or self.text}</label>
            <button class="icon-button context-help" data-url="{self.help_url}" type="button">
              <span class="glyphicon glyphicon-info-sign"></span>
            </button>
          </div>"""
        )



class MetaFormHelpRenderer(DefaultMeta):

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

    help_data, help_enabled = load_help.__func__()

    def bind_field(self, form, unbound_field, options=dict()):
        bound_field = super().bind_field(form, unbound_field, options)
        if getattr(bound_field, "help", None):
            bound_field.label = HelpLabel(
                bound_field.id, bound_field.label.text, bound_field.help
            )
        return bound_field
