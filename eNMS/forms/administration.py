from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    DateField,
    FloatField,
    HiddenField,
    IntegerField,
    PasswordField,
    SelectField,
    StringField,
    SelectMultipleField,
)

from eNMS.forms import metaform
from eNMS.forms.fields import MultipleInstanceField
from eNMS.properties import import_classes, user_permissions


class ParametersForm:
    action = "saveParameters"


class ViewParametersForm(FlaskForm, ParametersForm, metaclass=metaform):
    form_type = HiddenField(default="view")
    default_longitude = FloatField("Default Longitude")
    default_latitude = FloatField("Default Latitude")
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


class ClusterParametersForm(FlaskForm, ParametersForm, metaclass=metaform):
    form_type = HiddenField(default="cluster")
    cluster_scan_protocol = SelectField(choices=(("http", "HTTP"), ("https", "HTTPS")))
    cluster_scan_subnet = StringField("Cluster Scan Subnet")
    cluster_scan_timeout = FloatField("Cluster Scan Timeout")


class GitParametersForm(FlaskForm, ParametersForm, metaclass=metaform):
    form_type = HiddenField(default="git")
    git_configurations = StringField("Git Configurations Repository")
    git_automation = StringField("Git Automation Repository")


class SshParametersForm(FlaskForm, ParametersForm, metaclass=metaform):
    form_type = HiddenField(default="ssh")
    gotty_start_port = FloatField("Start port")
    gotty_end_port = FloatField("End port")


class NotificationsParametersForm(FlaskForm, ParametersForm, metaclass=metaform):
    form_type = HiddenField(default="notifications")
    mail_sender = StringField("Mail Sender Address")
    mail_recipients = StringField("Mail Recipients (separated by comma)")
    mattermost_url = StringField("Mattermost URL")
    mattermost_channel = StringField("Mattermost Channel")
    mattermost_verify_certificate = BooleanField("Mattermost: verify certificate")
    slack_token = StringField("Slack Token")
    slack_channel = StringField("Slack Channel")


class DatabaseDeletionForm(FlaskForm, metaclass=metaform):
    action = "databaseDeletion"
    form_type = HiddenField(default="database_deletion")
    clear_logs_date = DateField("Clear Logs Older than")
    deletion_choices = [(p, p) for p in import_classes]
    deletion_types = SelectMultipleField(
        "Instances to delete", choices=deletion_choices
    )


class InstanceDeletionForm(FlaskForm, metaclass=metaform):
    template = "instance_deletion"
    form_type = HiddenField(default="instance_deletion")


class ServerForm(FlaskForm, metaclass=metaform):
    template = "object"
    form_type = HiddenField(default="server")
    id = HiddenField()
    name = StringField("Name")
    description = StringField("Description")
    ip_address = StringField("IP address")
    weight = IntegerField("Weigth")


class ServerFilteringForm(FlaskForm, metaclass=metaform):
    action = "filter"
    form_type = HiddenField(default="server_filtering")
    name = StringField("Name")
    description = StringField("Description")
    ip_address = StringField("IP address")
    weight = StringField("Weigth")
    status = StringField("Status")


class LoginForm(FlaskForm, metaclass=metaform):
    form_type = HiddenField(default="login")
    authentication_method = SelectField("Authentication Method", choices=())
    name = StringField("Name")
    password = PasswordField("Password")


class DatabaseMigrationsForm(FlaskForm, metaclass=metaform):
    template = "database_migration"
    form_type = HiddenField(default="database_migration")
    empty_database_before_import = BooleanField("Empty Database before Import")
    export_choices = [(p, p) for p in import_classes]
    import_export_types = SelectMultipleField(
        "Instances to migrate", choices=export_choices
    )


class UserForm(FlaskForm, metaclass=metaform):
    template = "object"
    form_type = HiddenField(default="user")
    id = HiddenField()
    name = StringField("Name")
    password = PasswordField("Password")
    email = StringField("Email")
    permission_choices = [(p, p) for p in user_permissions]
    permissions = SelectMultipleField("Permissions", choices=permission_choices)
    pools = MultipleInstanceField("Pools", instance_type="Pool")


class UserFilteringForm(FlaskForm, metaclass=metaform):
    action = "filter"
    form_type = HiddenField(default="user_filtering")
    name = StringField("Name")
    email = StringField("Email")


class LogFilteringForm(FlaskForm, metaclass=metaform):
    action = "filter"
    form_type = HiddenField(default="log_filtering")
    source_ip_address = StringField("Source IP Address")
    content = StringField("Content")
