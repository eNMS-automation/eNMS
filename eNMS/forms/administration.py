from wtforms.validators import InputRequired
from wtforms.widgets import TextArea

from eNMS.forms import BaseForm, choices, configure_relationships, form_properties
from eNMS.forms.fields import (
    BooleanField,
    HiddenField,
    IntegerField,
    JsonField,
    MultipleInstanceField,
    PasswordField,
    StringField,
    SelectField,
    SelectMultipleField,
    SelectMultipleStringField,
)
from eNMS.setup import settings, themes


class SettingsForm(BaseForm):
    form_type = HiddenField(default="settings_panel")
    action = "eNMS.administration.saveSettings"
    settings = JsonField("Settings")
    write_changes = BooleanField("Write changes back to 'settings.json' file")


class AdminForm(BaseForm):
    template = "administration"
    form_type = HiddenField(default="administration")


class FilesForm(BaseForm):
    template = "files"
    form_type = HiddenField(default="files")


class UploadFilesForm(BaseForm):
    template = "upload_files"
    folder = HiddenField()
    form_type = HiddenField(default="upload_files")


class ResultLogDeletionForm(BaseForm):
    action = "eNMS.administration.resultLogDeletion"
    form_type = HiddenField(default="result_log_deletion")
    deletion_types = SelectMultipleField(
        "Instances do delete", choices=[("run", "result"), ("changelog", "changelog")],
    )
    date_time = StringField(type="date", label="Delete Records before")


class ServerForm(BaseForm):
    template = "object"
    form_type = HiddenField(default="server")
    id = HiddenField()
    name = StringField("Name", [InputRequired()])
    description = StringField("Description")
    ip_address = StringField("IP address")
    weight = IntegerField("Weigth")


class LoginForm(BaseForm):
    form_type = HiddenField(default="login")
    authentication_method = SelectField("Authentication Method", choices=())
    name = StringField("Name", [InputRequired()])
    password = PasswordField("Password", [InputRequired()])


class ImportService(BaseForm):
    action = "eNMS.administration.importService"
    form_type = HiddenField(default="import_service")
    import_services = SelectField("Service", choices=())


class ChangelogForm(BaseForm):
    template = "object"
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


def init_variable_forms(app):
    def configure_access_form(cls):
        cls.models = app.rbac["models"]
        for model, access_rights in cls.models.items():
            setattr(cls, model, MultipleInstanceField())
            form_properties["access"][model] = {"type": "object-list"}
            access_field = SelectMultipleStringField(choices=choices(access_rights))
            form_properties["access"][f"{model}_access"] = {
                "type": "multiselect-string"
            }
            setattr(cls, f"{model}_access", access_field)
        return cls

    class RbacForm(BaseForm):
        template = "object"
        form_type = HiddenField(default="rbac")
        id = HiddenField()
        name = StringField("Name", [InputRequired()])
        email = StringField("Email")

    @configure_relationships("groups")
    class UserForm(RbacForm):
        form_type = HiddenField(default="user")
        is_admin = BooleanField(default=False)
        authentication = SelectField(
            "Authentication Method",
            choices=[
                (method, values["display_name"])
                for method, values in settings["authentication"]["methods"].items()
            ],
        )
        theme = SelectField(
            "Theme",
            choices=[
                (theme, values["name"]) for theme, values in themes["themes"].items()
            ],
        )
        password = PasswordField("Password")

    @configure_relationships("users")
    class GroupForm(RbacForm):
        form_type = HiddenField(default="group")

    @configure_relationships("users", "groups")
    @configure_access_form
    class AccessForm(RbacForm):
        template = "access"
        form_type = HiddenField(default="access")
        description = StringField("Description")
        menu = SelectMultipleField("Menu", choices=choices(list(app.rbac["menu"])))
        pages = SelectMultipleField("Pages", choices=choices(app.rbac["pages"]))
        upper_menu = SelectMultipleField(
            "Upper Menu", choices=choices(app.rbac["upper_menu"])
        )
        get_requests = SelectMultipleField(
            "GET requests", choices=choices(app.rbac["get_requests"])
        )
        post_requests = SelectMultipleField(
            "POST requests", choices=choices(app.rbac["post_requests"])
        )
        relations = ["pools", "services"]

    class DatabaseMigrationsForm(BaseForm):
        template = "database_migration"
        form_type = HiddenField(default="database_migration")
        empty_database_before_import = BooleanField("Empty Database before Import")
        skip_pool_update = BooleanField(
            "Skip the Pool update after Import", default="checked"
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
