from eNMS.automation.forms import (
    AddJobsForm,
    CompareResultsForm,
    JobForm,
    LogAutomationForm,
)
from eNMS.inventory.forms import (
    CompareConfigurationsForm,
    ConnectionForm,
    DeviceAutomationForm,
    DeviceFilteringForm,
    DeviceForm,
    LinkForm,
    LinkFilteringForm,
    PoolForm,
    PoolObjectsForm,
)
from eNMS.scheduling.forms import TaskForm


from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    FloatField,
    HiddenField,
    IntegerField,
    SelectField,
    StringField,
    PasswordField,
    SelectMultipleField,
)

from eNMS.models.base_models import MultipleObjectField
from eNMS.properties import import_properties, user_permissions


class LoginForm(FlaskForm):
    authentication_method = SelectField(choices=())
    name = StringField()
    password = PasswordField()


class UserForm(FlaskForm):
    list_fields = HiddenField(default="permissions")
    id = HiddenField()
    name = StringField()
    password = PasswordField()
    email = StringField()
    permission_choices = [(p, p) for p in user_permissions]
    permissions = SelectMultipleField(choices=permission_choices)
    pools = MultipleObjectField("Pool")


class AdministrationForm(FlaskForm):
    boolean_fields = HiddenField(default="mattermost_verify_certificate")
    cluster_scan_protocol = SelectField(choices=(("http", "HTTP"), ("https", "HTTPS")))
    cluster_scan_subnet = StringField()
    cluster_scan_timeout = FloatField()
    default_longitude = FloatField()
    default_latitude = FloatField()
    default_zoom_level = IntegerField()
    default_view = SelectField(choices=(("2D", "2D"), ("2DC", "2DC"), ("3D", "3D")))
    default_marker = SelectField(
        choices=(
            ("Image", "Image"),
            ("Circle", "Circle"),
            ("Circle Marker", "Circle Marker"),
        )
    )
    git_configurations = StringField()
    git_automation = StringField()
    gotty_start_port = FloatField("Start port")
    gotty_end_port = FloatField("End port")
    mail_sender = StringField()
    mail_recipients = StringField()
    mattermost_url = StringField("Mattermost URL")
    mattermost_channel = StringField()
    mattermost_verify_certificate = BooleanField()
    slack_token = StringField()
    slack_channel = StringField()
    categories = {
        "Geographical Parameters": (
            "default_longitude",
            "default_latitude",
            "default_zoom_level",
            "default_view",
            "default_marker",
        ),
        "SSH Terminal Parameters": ("gotty_start_port", "gotty_end_port"),
        "Notification Parameters": (
            "mail_sender",
            "mail_recipients",
            "slack_token",
            "slack_channel",
            "mattermost_url",
            "mattermost_channel",
            "mattermost_verify_certificate",
        ),
        "Gitlab Parameters": ("git_automation", "git_configurations"),
        "Cluster Management": (
            "cluster_scan_subnet",
            "cluster_scan_protocol",
            "cluster_scan_timeout",
        ),
    }


class MigrationsForm(FlaskForm):
    boolean_fields = HiddenField(default="empty_database_before_import")
    list_fields = HiddenField(default="import_export_types")
    empty_database_before_import = BooleanField()
    export_choices = [(p, p) for p in import_properties]
    import_export_types = SelectMultipleField(choices=export_choices)


class DatabaseHelpersForm(FlaskForm):
    list_fields = HiddenField(default="deletion_types")
    clear_logs_date = StringField()
    deletion_choices = [(p, p) for p in import_properties]
    deletion_types = SelectMultipleField(choices=deletion_choices)


class InstanceForm(FlaskForm):
    id = HiddenField()
    name = StringField()
    description = StringField()
    ip_address = StringField("IP address")
    weight = IntegerField()


form_classes = {
    "add_jobs": AddJobsForm,
    "configuration": CompareConfigurationsForm,
    "configuration_filtering": DeviceFilteringForm,
    "connection": ConnectionForm,
    "device": DeviceForm,
    "device_automation": DeviceAutomationForm,
    "device_filtering": DeviceFilteringForm,
    "instance": InstanceForm,
    "link": LinkForm,
    "link_filtering": LinkFilteringForm,
    "logrule": LogAutomationForm,
    "pool": PoolForm,
    "pool_objects": PoolObjectsForm,
    "results": CompareResultsForm,
    "user": UserForm,
    "service": JobForm,
    "task": TaskForm,
    "workflow": JobForm,
}

form_templates = {
    "configuration_filtering": "filtering_form",
    "device": "base_form",
    "device_filtering": "filtering_form",
    "instance": "base_form",
    "link": "base_form",
    "link_filtering": "filtering_form",
    "task": "base_form",
    "user": "base_form",
}

form_properties = {
    "add_jobs": ("add_jobs",),
    "advanced": ("clear_logs_date", "deletion_types", "import_export_types"),
    "configuration_filtering": ("pools",),
    "device_automation": ("jobs",),
    "device_filtering": ("pools",),
    "link": ("link-source", "link-destination"),
    "link_filtering": ("pools",),
    "logrule": ("jobs",),
    "pool_objects": ("devices", "links"),
    "service": ("devices", "pools"),
    "task": ("start_date", "end_date", "job"),
    "user": ("permissions", "pools"),
    "workflow": ("devices", "pools"),
}
