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
from eNMS.forms.fields import MultipleObjectField
from eNMS.properties import import_properties, user_permissions


class ParametersForm:
    action = "saveParameters"


class ViewParametersForm(FlaskForm, ParametersForm, metaclass=metaform):
    form_type = HiddenField(default="view")
    default_longitude = FloatField()
    default_latitude = FloatField()
    default_zoom_level = IntegerField()
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
    cluster_scan_subnet = StringField()
    cluster_scan_timeout = FloatField()


class GitParametersForm(FlaskForm, ParametersForm, metaclass=metaform):
    form_type = HiddenField(default="git")
    git_configurations = StringField()
    git_automation = StringField()


class SshParametersForm(FlaskForm, ParametersForm, metaclass=metaform):
    form_type = HiddenField(default="ssh")
    gotty_start_port = FloatField("Start port")
    gotty_end_port = FloatField("End port")


class NotificationsParametersForm(FlaskForm, ParametersForm, metaclass=metaform):
    form_type = HiddenField(default="notifications")
    mail_sender = StringField()
    mail_recipients = StringField()
    mattermost_url = StringField("Mattermost URL")
    mattermost_channel = StringField()
    mattermost_verify_certificate = BooleanField()
    slack_token = StringField()
    slack_channel = StringField()


class DatabaseDeletionForm(FlaskForm, metaclass=metaform):
    action = "databaseDeletion"
    form_type = HiddenField(default="database_deletion")
    clear_logs_date = DateField()
    deletion_choices = [(p, p) for p in import_properties]
    deletion_types = SelectMultipleField(choices=deletion_choices)


class InstanceForm(FlaskForm, metaclass=metaform):
    template = "object"
    form_type = HiddenField(default="instance")
    id = HiddenField()
    name = StringField()
    description = StringField()
    ip_address = StringField("IP address")
    weight = IntegerField()


class InstanceFilteringForm(FlaskForm, metaclass=metaform):
    action = "filter"
    form_type = HiddenField(default="instance_filtering")
    name = StringField()
    description = StringField()
    ip_address = StringField("IP address")
    weight = StringField()


class LoginForm(FlaskForm, metaclass=metaform):
    form_type = HiddenField(default="login")
    authentication_method = SelectField(choices=())
    name = StringField()
    password = PasswordField()


class MigrationsForm(FlaskForm, metaclass=metaform):
    template = "migration"
    form_type = HiddenField(default="migration")
    empty_database_before_import = BooleanField()
    export_choices = [(p, p) for p in import_properties]
    import_export_types = SelectMultipleField(choices=export_choices)


class UserForm(FlaskForm, metaclass=metaform):
    template = "object"
    form_type = HiddenField(default="user")
    id = HiddenField()
    name = StringField()
    password = PasswordField()
    email = StringField()
    permission_choices = [(p, p) for p in user_permissions]
    permissions = SelectMultipleField(choices=permission_choices)
    pools = MultipleObjectField("Pool")


class UserFilteringForm(FlaskForm, metaclass=metaform):
    action = "filter"
    form_type = HiddenField(default="user_filtering")
    name = StringField()
    email = StringField()


class LogFilteringForm(FlaskForm, metaclass=metaform):
    action = "filter"
    form_type = HiddenField(default="log_filtering")
    source_ip_address = StringField()
    content = StringField()
