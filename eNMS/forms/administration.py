from wtforms.validators import InputRequired
from wtforms.widgets import TextArea

from eNMS.database import db
from eNMS.forms import BaseForm, choices, configure_relationships
from eNMS.forms.fields import (
    BooleanField,
    HiddenField,
    IntegerField,
    JsonField,
    PasswordField,
    StringField,
    SelectField,
    SelectMultipleField,
)


class SettingsForm(BaseForm):
    form_type = HiddenField(default="settings_panel")
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


class DatabaseDeletionForm(BaseForm):
    action = "eNMS.administration.databaseDeletion"
    form_type = HiddenField(default="database_deletion")
    deletion_choices = [(p, p) for p in db.import_classes]
    deletion_types = SelectMultipleField(
        "Instances to delete", choices=deletion_choices
    )


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


class DatabaseMigrationsForm(BaseForm):
    template = "database_migration"
    form_type = HiddenField(default="database_migration")
    empty_database_before_import = BooleanField("Empty Database before Import")
    skip_update_pools_after_import = BooleanField(
        "Skip the Pool update after Import", default="checked"
    )
    export_choices = [(p, p) for p in db.import_classes]
    import_export_types = SelectMultipleField(
        "Instances to migrate", choices=export_choices
    )


class ImportService(BaseForm):
    action = "eNMS.administration.importService"
    form_type = HiddenField(default="import_service")
    service = SelectField("Service", choices=())


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


def init_rbac_form(rbac):
    class RbacForm(BaseForm):
        template = "object"
        form_type = HiddenField(default="rbac")
        id = HiddenField()
        name = StringField("Name", [InputRequired()])
        email = StringField("Email")
        menu = SelectMultipleField("Menu", choices=choices(list(rbac["menu"])))
        pages = SelectMultipleField("Pages", choices=choices(rbac["pages"]))
        upper_menu = SelectMultipleField(
            "Upper Menu", choices=choices(rbac["upper_menu"])
        )
        get_requests = SelectMultipleField(
            "GET requests", choices=choices(rbac["get_requests"])
        )
        post_requests = SelectMultipleField(
            "POST requests", choices=choices(rbac["post_requests"])
        )

    @configure_relationships("groups")
    class UserForm(RbacForm):
        form_type = HiddenField(default="user")
        manual_rbac = BooleanField("Manually defined RBAC")
        password = PasswordField("Password")

    @configure_relationships("users", "pools", "services")
    class GroupForm(RbacForm):
        form_type = HiddenField(default="group")
