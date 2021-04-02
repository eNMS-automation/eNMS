from collections import defaultdict
from flask import request
from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms.fields.core import UnboundField
from wtforms.form import FormMeta
from wtforms.validators import InputRequired
from wtforms.widgets import TextArea

from eNMS import app
from eNMS.database import db
from eNMS.forms.fields import (
    BooleanField,
    HiddenField,
    DictField,
    InstanceField,
    IntegerField,
    JsonField,
    MultipleInstanceField,
    PasswordField,
    SelectField,
    SelectMultipleField,
    SelectMultipleStringField,
    StringField,
)
from eNMS.models import property_types, relationships
from eNMS.setup import settings, themes

form_classes = {}
form_properties = defaultdict(dict)


class MetaForm(FormMeta):
    def __new__(cls, name, bases, attrs):
        if name == "BaseForm":
            return type.__new__(cls, name, bases, attrs)
        form_type = attrs["form_type"].kwargs["default"]
        form = type.__new__(cls, name, bases, attrs)
        if form.__dict__.get("get_request_allowed", True):
            app.rbac["get_requests"][f"/{form_type}_form"] = "access"
        if hasattr(form, "form_init"):
            form.form_init()
        if not hasattr(form, "custom_properties"):
            form.custom_properties = {}
        form.custom_properties = {
            **form.custom_properties,
            **app.properties["custom"].get(form_type, {}),
        }
        for property, values in form.custom_properties.items():
            if not values.get("form", True):
                continue
            if property in db.private_properties_set:
                field = PasswordField
            else:
                field = {
                    "boolean": BooleanField,
                    "dict": DictField,
                    "integer": IntegerField,
                    "json": JsonField,
                    "string": StringField,
                    "select": SelectField,
                    "multiselect": SelectMultipleField,
                }[values.get("type", "string")]
            form_kw = {"default": values["default"]} if "default" in values else {}
            if field in (SelectField, SelectMultipleField):
                form_kw["choices"] = values["choices"]
            field = field(values["pretty_name"], **form_kw)
            setattr(form, property, field)
            attrs[property] = field
        form_classes[form_type] = form
        properties = {}
        for field_name, field in attrs.items():
            if not isinstance(field, UnboundField):
                continue
            field_type = field.kwargs.pop("type", None)
            if not field_type:
                field_type = field.field_class.type
            properties[field_name] = {
                "type": field_type,
                "model": field.kwargs.pop("model", None),
            }
            if field.args and isinstance(field.args[0], str):
                app.property_names[field_name] = field.args[0]
            if (
                issubclass(field.field_class, PasswordField)
                and field_name not in db.private_properties_set
            ):
                db.private_properties_set.add(field_name)
        form_properties[form_type].update(properties)
        for property, value in properties.items():
            if property not in property_types and value["type"] != "field-list":
                property_types[property] = value["type"]
        for base in form.__bases__:
            if not hasattr(base, "form_type"):
                continue
            base_form_type = base.form_type.kwargs["default"]
            form.custom_properties.update(base.custom_properties)
            if base_form_type == "service":
                form.service_fields = [
                    property
                    for property in properties
                    if property not in form.custom_properties
                ]
            if getattr(base, "abstract_service", False):
                form.service_fields.extend(form_properties[base_form_type])
            form_properties[form_type].update(form_properties[base_form_type])
        return form

    def __setattr__(self, field, value):
        if hasattr(value, "field_class") and "multiselect" in value.field_class.type:
            form_type = self.form_type.kwargs["default"]
            form_properties[form_type][field] = {"type": value.field_class.type}
        return super().__setattr__(field, value)


class BaseForm(FlaskForm, metaclass=MetaForm):
    @classmethod
    def configure_relationships(cls, *models):
        form_type = cls.form_type.kwargs["default"]
        for related_model, relation in relationships[form_type].items():
            if related_model not in models:
                continue
            field = MultipleInstanceField if relation["list"] else InstanceField
            field_type = "object-list" if relation["list"] else "object"
            form_properties[form_type][related_model] = {"type": field_type}
            setattr(cls, related_model, field())

    def form_postprocessing(self, form_data):
        data = {**form_data.to_dict(), **{"user": current_user}}
        if request.files:
            data["file"] = request.files["file"]
        for property, field in form_properties[form_data.get("form_type")].items():
            if field["type"] in ("object-list", "multiselect", "multiselect-string"):
                value = form_data.getlist(property)
                if field["type"] == "multiselect-string":
                    value = str(value)
                data[property] = value
            elif field["type"] == "object":
                data[property] = form_data.get(property)
            elif field["type"] == "field-list":
                data[property] = []
                for entry in getattr(self, property):
                    properties = entry.data
                    properties.pop("csrf_token")
                    data[property].append(properties)
            elif field["type"] == "bool":
                data[property] = property in form_data
            elif field["type"] in db.field_conversion and property in data:
                data[property] = db.field_conversion[field["type"]](form_data[property])
        return data


def choices(iterable):
    return [(choice, choice) for choice in iterable]


class SettingsForm(BaseForm):
    form_type = HiddenField(default="settings_panel")
    action = "eNMS.administration.saveSettings"
    settings = JsonField("Settings")
    write_changes = BooleanField("Write changes back to 'settings.json' file")


class AdminForm(BaseForm):
    template = "administration"
    form_type = HiddenField(default="administration")


class DebugForm(BaseForm):
    template = "debug"
    form_type = HiddenField(default="debug")
    snippets = SelectField(validate_choice=False)
    code = StringField(
        "Python Code",
        type="code",
        python=True,
        widget=TextArea(),
        render_kw={"rows": 15},
    )
    output = StringField("Output", widget=TextArea(), render_kw={"rows": 16})


class UploadFilesForm(BaseForm):
    template = "upload_files"
    folder = HiddenField()
    form_type = HiddenField(default="upload_files")


class ResultLogDeletionForm(BaseForm):
    action = "eNMS.administration.resultLogDeletion"
    form_type = HiddenField(default="result_log_deletion")
    deletion_types = SelectMultipleField(
        "Instances do delete",
        choices=[("run", "result"), ("changelog", "changelog")],
    )
    date_time = StringField(type="date", label="Delete Records before")


class ServerForm(BaseForm):
    action = "eNMS.base.processData"
    form_type = HiddenField(default="server")
    id = HiddenField()
    name = StringField("Name", [InputRequired()])
    description = StringField(widget=TextArea(), render_kw={"rows": 6})
    ip_address = StringField("IP address")
    weight = IntegerField("Weigth", default=1)


class CredentialForm(BaseForm):
    action = "eNMS.base.processData"
    form_type = HiddenField(default="credential")
    id = HiddenField()
    name = StringField("Name", [InputRequired()])
    description = StringField(widget=TextArea(), render_kw={"rows": 6})
    role = SelectField(
        "Role",
        choices=(
            ("read-write", "Read Write"),
            ("read-only", "Read Only"),
        ),
    )
    subtype = SelectField(
        "Subtype", choices=(("password", "Username / Password"), ("key", "SSH Key"))
    )
    device_pools = MultipleInstanceField("Devices", model="pool")
    user_pools = MultipleInstanceField("Users", model="pool")
    priority = IntegerField("Priority", default=1)
    username = StringField("Username")
    password = PasswordField("Password")
    private_key = StringField(widget=TextArea(), render_kw={"rows": 1})
    enable_password = PasswordField("'Enable' Password")


class LoginForm(BaseForm):
    form_type = HiddenField(default="login")
    get_request_allowed = False
    authentication_method = SelectField("Authentication Method", choices=())
    username = StringField("Name", [InputRequired()])
    password = PasswordField("Password", [InputRequired()])


class ImportService(BaseForm):
    action = "eNMS.administration.importService"
    form_type = HiddenField(default="import_service")
    service = SelectField("Service", choices=())


class ChangelogForm(BaseForm):
    action = "eNMS.base.processData"
    form_type = HiddenField(default="changelog")
    id = HiddenField()
    severity = SelectField(
        "Severity",
        choices=(
            ("debug", "Debug"),
            ("info", "Info"),
            ("warning", "Warning"),
            ("error", "Error"),
            ("critical", "Critical"),
        ),
    )
    content = StringField(widget=TextArea(), render_kw={"rows": 10})


class RbacForm(BaseForm):
    action = "eNMS.base.processData"
    form_type = HiddenField(default="rbac")
    get_request_allowed = False
    id = HiddenField()
    name = StringField("Name", [InputRequired()])
    description = StringField(widget=TextArea(), render_kw={"rows": 6})
    email = StringField("Email")


class UserForm(RbacForm):
    form_type = HiddenField(default="user")
    groups = StringField("Groups")
    theme = SelectField(
        "Theme",
        choices=[(theme, values["name"]) for theme, values in themes["themes"].items()],
    )
    authentication = SelectField(
        "Authentication",
        choices=[
            (method, values["display_name"])
            for method, values in settings["authentication"]["methods"].items()
        ],
    )
    password = PasswordField("Password")
    is_admin = BooleanField(default=False)


class AccessForm(RbacForm):
    template = "access"
    form_type = HiddenField(default="access")
    user_pools = MultipleInstanceField("pool")
    access_pools = MultipleInstanceField("pool")
    access_type = SelectMultipleStringField(
        "Access Type",
        choices=choices(
            ["Read", "Edit", "Run", "Schedule", "Connect", "Use as target"]
        ),
    )
    relations = ["pools", "services"]

    @classmethod
    def form_init(cls):
        cls.configure_relationships("users")
        keys = ("get_requests", "post_requests", "delete_requests", "upper_menu")
        for key in keys:
            values = [(k, k) for k, v in app.rbac[key].items() if v == "access"]
            field_name = " ".join(key.split("_")).capitalize()
            setattr(cls, key, SelectMultipleField(field_name, choices=values))
        menus, pages = [], []
        for category, values in app.rbac["menu"].items():
            if values["rbac"] == "admin":
                continue
            if values["rbac"] == "access":
                menus.append(category)
            for page, page_values in values["pages"].items():
                if page_values["rbac"] == "admin":
                    continue
                if page_values["rbac"] == "access":
                    pages.append(page)
                subpages = page_values.get("subpages", {})
                for subpage, subpage_values in subpages.items():
                    if subpage_values["rbac"] == "admin":
                        continue
                    if subpage_values["rbac"] == "access":
                        pages.append(subpage)
        setattr(cls, "menu", SelectMultipleField("Menu", choices=choices(menus)))
        setattr(cls, "pages", SelectMultipleField("Pages", choices=choices(pages)))


class DatabaseMigrationsForm(BaseForm):
    template = "database_migration"
    form_type = HiddenField(default="database_migration")
    empty_database_before_import = BooleanField("Empty Database before Import")
    skip_pool_update = BooleanField(
        "Skip the Pool update after Import", default="checked"
    )
    export_private_properties = BooleanField(
        "Include private properties", default="checked"
    )
    export_choices = [(p, p) for p in app.database["import_export_models"]]
    import_export_types = SelectMultipleField(
        "Instances to migrate", choices=export_choices
    )


class DatabaseDeletionForm(BaseForm):
    action = "eNMS.administration.databaseDeletion"
    form_type = HiddenField(default="database_deletion")
    deletion_choices = [(p, p) for p in app.database["import_export_models"]]
    deletion_types = SelectMultipleField(
        "Instances to delete", choices=deletion_choices
    )
