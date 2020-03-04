from wtforms.validators import InputRequired
from wtforms.widgets import TextArea

from eNMS import app
from eNMS.forms import BaseForm, configure_relationships, set_custom_properties
from eNMS.forms.fields import (
    BooleanField,
    HiddenField,
    IntegerField,
    PasswordField,
    StringField,
    SelectField,
    SelectMultipleField,
)
from eNMS.properties.database import import_classes


class SettingsForm(BaseForm):
    action = "eNMS.administration.saveSettings"
    form_type = HiddenField(default="settings")


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
    deletion_choices = [(p, p) for p in import_classes]
    deletion_types = SelectMultipleField(
        "Instances to delete", choices=deletion_choices
    )


class ResultLogDeletionForm(BaseForm):
    action = "eNMS.administration.resultLogDeletion"
    form_type = HiddenField(default="result_log_deletion")
    deletion_types = SelectMultipleField(
        "Instances do delete",
        choices=[("result", "result"), ("changelog", "changelog")],
    )
    date_time = StringField(type="date", label="Delete Records before")


@set_custom_properties
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
    password = PasswordField("Password")


class DatabaseMigrationsForm(BaseForm):
    template = "database_migration"
    form_type = HiddenField(default="database_migration")
    empty_database_before_import = BooleanField("Empty Database before Import")
    skip_update_pools_after_import = BooleanField(
        "Skip the Pool update after Import", default="checked"
    )
    export_choices = [(p, p) for p in import_classes]
    import_export_types = SelectMultipleField(
        "Instances to migrate", choices=export_choices
    )


class ImportService(BaseForm):
    action = "eNMS.administration.importService"
    form_type = HiddenField(default="import_service")
    service = SelectField("Service", choices=())


@set_custom_properties
@configure_relationships
class UserForm(BaseForm):
    template = "object"
    form_type = HiddenField(default="user")
    id = HiddenField()
    name = StringField("Name", [InputRequired()])
    password = PasswordField("Password")
    email = StringField("Email")
    group = SelectField("Permissions", choices=[(g, g) for g in app.rbac["groups"]])


@set_custom_properties
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
