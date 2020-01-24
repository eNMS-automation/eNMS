from wtforms import (
    BooleanField,
    HiddenField,
    IntegerField,
    PasswordField,
    SelectField,
    StringField,
    SelectMultipleField,
)
from wtforms.validators import InputRequired

from eNMS.forms import BaseForm, configure_relationships
from eNMS.properties.database import import_classes


class ConfigurationForm(BaseForm):
    action = "saveConfiguration"
    form_type = HiddenField(default="configuration")


class DatabaseDeletionForm(BaseForm):
    action = "databaseDeletion"
    form_type = HiddenField(default="database_deletion")
    deletion_choices = [(p, p) for p in import_classes]
    deletion_types = SelectMultipleField(
        "Instances to delete", choices=deletion_choices
    )


class InstanceDeletionForm(BaseForm):
    template = "instance_deletion"
    form_type = HiddenField(default="instance_deletion")


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
    skip_update_pools_after_import = BooleanField("Skip the Pool update after Import", default="checked")
    export_choices = [(p, p) for p in import_classes]
    import_export_types = SelectMultipleField(
        "Instances to migrate", choices=export_choices
    )


class ImportService(BaseForm):
    action = "importService"
    form_type = HiddenField(default="import_service")
    service = SelectField("Service", choices=())


@configure_relationships
class UserForm(BaseForm):
    template = "object"
    form_type = HiddenField(default="user")
    id = HiddenField()
    name = StringField("Name", [InputRequired()])
    password = PasswordField("Password")
    email = StringField("Email")
    permission_choices = [
        ("Admin", "Admin"),
        ("Connect to device", "Connect to device"),
        ("View", "View"),
        ("Edit", "Edit"),
    ]
    permissions = SelectMultipleField("Permissions", choices=permission_choices)
