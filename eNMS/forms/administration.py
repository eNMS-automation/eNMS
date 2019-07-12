from wtforms import (
    BooleanField,
    FloatField,
    HiddenField,
    IntegerField,
    PasswordField,
    SelectField,
    StringField,
    SelectMultipleField,
)

from eNMS.forms import BaseForm
from eNMS.forms.fields import (
    DateField,
    MultipleInstanceField,
    NoValidationSelectMultipleField,
)
from eNMS.properties.database import import_classes


class ParametersForm:
    action = "saveParameters"


class ViewParametersForm(BaseForm, ParametersForm):
    form_type = HiddenField(default="view")
    default_longitude = StringField("Default Longitude")
    default_latitude = StringField("Default Latitude")
    default_zoom_level = IntegerField("Default Zoom Level")
    default_view = SelectField(
        choices=(("2D", "2D"), ("2DC", "Clusterized 2D"), ("3D", "3D"))
    )
    default_marker = SelectField(
        choices=(
            ("Image", "Image"),
            ("Circle", "Circle"),
            ("Circle Marker", "Circle Marker"),
        )
    )


class ClusterParametersForm(BaseForm, ParametersForm):
    form_type = HiddenField(default="cluster")
    cluster_scan_protocol = SelectField(choices=(("http", "HTTP"), ("https", "HTTPS")))
    cluster_scan_subnet = StringField("Cluster Scan Subnet")
    cluster_scan_timeout = FloatField("Cluster Scan Timeout")


class GitParametersForm(BaseForm, ParametersForm):
    form_type = HiddenField(default="git")
    git_configurations = StringField("Git Configurations Repository")
    git_automation = StringField("Git Automation Repository")


class SshParametersForm(BaseForm, ParametersForm):
    form_type = HiddenField(default="ssh")
    gotty_start_port = FloatField("Start port")
    gotty_end_port = FloatField("End port")


class NotificationsParametersForm(BaseForm, ParametersForm):
    form_type = HiddenField(default="notifications")
    mail_sender = StringField("Mail Sender Address")
    mail_recipients = StringField("Mail Recipients (separated by comma)")
    mattermost_url = StringField("Mattermost URL")
    mattermost_channel = StringField("Mattermost Channel")
    mattermost_verify_certificate = BooleanField("Mattermost: verify certificate")
    slack_token = StringField("Slack Token")
    slack_channel = StringField("Slack Channel")


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
    name = StringField("Name")
    description = StringField("Description")
    ip_address = StringField("IP address")
    weight = IntegerField("Weigth")


class LoginForm(BaseForm):
    form_type = HiddenField(default="login")
    authentication_method = SelectField("Authentication Method", choices=())
    name = StringField("Name")
    password = PasswordField("Password")


class DatabaseMigrationsForm(BaseForm):
    template = "database_migration"
    form_type = HiddenField(default="database_migration")
    empty_database_before_import = BooleanField("Empty Database before Import")
    export_choices = [(p, p) for p in import_classes]
    import_export_types = SelectMultipleField(
        "Instances to migrate", choices=export_choices
    )


class ImportJobs(BaseForm):
    action = "importJobs"
    form_type = HiddenField(default="import_jobs")
    jobs_to_import = NoValidationSelectMultipleField("Jobs to import", choices=())


class UserForm(BaseForm):
    template = "object"
    form_type = HiddenField(default="user")
    id = HiddenField()
    name = StringField("Name")
    password = PasswordField("Password")
    email = StringField("Email")
    permission_choices = [
        ("Admin", "Admin"),
        ("Connect to device", "Connect to device"),
        ("View", "View"),
        ("Edit", "Edit"),
    ]
    permissions = SelectMultipleField("Permissions", choices=permission_choices)
    pools = MultipleInstanceField("Pools", instance_type="Pool")
