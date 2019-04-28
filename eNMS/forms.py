from flask_wtf import FlaskForm
from typing import Any
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
from wtforms.fields.core import UnboundField

from eNMS.controller import controller
from eNMS.database import choices
from eNMS.properties import (
    custom_properties,
    pool_link_properties,
    link_subtypes,
    pool_device_properties,
    device_subtypes,
    import_properties,
    user_permissions,
)


class DateField(StringField):
    pass


class ObjectField(SelectField):
    def __init__(self, model: str, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.choices = choices(model)


class MultipleObjectField(SelectMultipleField):
    def __init__(self, model: str, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.choices = choices(model)


form_properties = {}

field_types = {
    DateField: "date",
    FloatField: "float",
    IntegerField: "integer",
    MultipleObjectField: "object-list",
    ObjectField: "object",
    SelectField: "list",
    SelectMultipleField: "multiselect",
}


def form_preprocessing(*args, **kwargs):
    cls = type(*args, **kwargs)
    form_properties[cls.form_type] = {
        field_name: field_types[field.field_class]
        for field_name, field in args[-1].items()
        if isinstance(field, UnboundField) and field.field_class in field_types
    }
    return cls


class LoginForm(FlaskForm, metaclass=form_preprocessing):
    form_type = HiddenField("login")
    authentication_method = SelectField(choices=())
    name = StringField()
    password = PasswordField()


class UserForm(FlaskForm, metaclass=form_preprocessing):
    form_type = HiddenField("user")
    id = HiddenField()
    name = StringField()
    password = PasswordField()
    email = StringField()
    permission_choices = [(p, p) for p in user_permissions]
    permissions = SelectMultipleField(choices=permission_choices)
    pools = MultipleObjectField("Pool")


class AdministrationForm(FlaskForm, metaclass=form_preprocessing):
    form_type = HiddenField("administration")
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


class MigrationsForm(FlaskForm, metaclass=form_preprocessing):
    form_type = HiddenField("migration")
    boolean_fields = HiddenField(default="empty_database_before_import")
    list_fields = HiddenField(default="import_export_types")
    empty_database_before_import = BooleanField()
    export_choices = [(p, p) for p in import_properties]
    import_export_types = SelectMultipleField(choices=export_choices)


class DatabaseHelpersForm(FlaskForm, metaclass=form_preprocessing):
    form_type = HiddenField("database_helpers")
    list_fields = HiddenField(default="deletion_types")
    clear_logs_date = DateField()
    deletion_choices = [(p, p) for p in import_properties]
    deletion_types = SelectMultipleField(choices=deletion_choices)


class InstanceForm(FlaskForm, metaclass=form_preprocessing):
    form_type = HiddenField("instance")
    id = HiddenField()
    name = StringField()
    description = StringField()
    ip_address = StringField("IP address")
    weight = IntegerField()


def configure_device_form(cls: FlaskForm) -> FlaskForm:
    for property in custom_properties:
        setattr(cls, property, StringField())
    return cls


def configure_pool_form(cls: FlaskForm) -> FlaskForm:
    cls.device_properties = pool_device_properties
    cls.link_properties = pool_link_properties
    for cls_name, properties in (
        ("device", pool_device_properties),
        ("link", pool_link_properties),
    ):
        for property in properties:
            match_field = f"{cls_name}_{property}_match"
            setattr(cls, f"{cls_name}_{property}", StringField(property))
            setattr(
                cls,
                match_field,
                SelectField(
                    choices=(
                        ("inclusion", "Inclusion"),
                        ("equality", "Equality"),
                        ("regex", "Regular Expression"),
                    )
                ),
            )
    return cls


class ConnectionForm(FlaskForm, metaclass=form_preprocessing):
    form_type = HiddenField("connection")
    address_choices = [("ip_address", "IP address"), ("name", "Name")] + [
        (property, values["pretty_name"])
        for property, values in custom_properties.items()
        if values.get("is_address", False)
    ]
    address = SelectField(choices=address_choices)


class ObjectForm(FlaskForm):
    name = StringField()
    description = StringField()
    location = StringField()
    vendor = StringField()
    model = StringField()


@configure_device_form
class DeviceForm(ObjectForm, metaclass=form_preprocessing):
    form_type = HiddenField("device")
    id = HiddenField()
    device_types = [subtype for subtype in device_subtypes.items()]
    subtype = SelectField(choices=device_types)
    ip_address = StringField("IP address")
    port = IntegerField(default=22)
    operating_system = StringField()
    os_version = StringField()
    longitude = FloatField(default=0.0)
    latitude = FloatField(default=0.0)
    username = StringField()
    password = PasswordField()
    enable_password = PasswordField()
    napalm_driver = SelectField(choices=controller.NAPALM_DRIVERS)
    netmiko_driver = SelectField(choices=controller.NETMIKO_DRIVERS)


class LinkForm(ObjectForm, metaclass=form_preprocessing):
    form_type = HiddenField("link")
    id = HiddenField()
    link_types = [subtype for subtype in link_subtypes.items()]
    subtype = SelectField(choices=link_types)
    source = ObjectField("Device")
    destination = ObjectField("Device")


class ObjectFilteringForm(FlaskForm):
    list_fields = HiddenField(default="pools")
    pools = MultipleObjectField("Pool")


@configure_device_form
class DeviceFilteringForm(
    ObjectForm, ObjectFilteringForm, metaclass=form_preprocessing
):
    form_type = HiddenField("device_filtering")
    current_configuration = StringField()
    subtype = StringField()
    ip_address = StringField()
    port = StringField()
    operating_system = StringField()
    os_version = StringField()
    longitude = StringField()
    latitude = StringField()
    napalm_driver = StringField()
    netmiko_driver = StringField()


class LinkFilteringForm(ObjectForm, ObjectFilteringForm, metaclass=form_preprocessing):
    form_type = HiddenField("link_filtering")
    subtype = StringField()
    source_name = StringField()
    destination_name = StringField()


@configure_pool_form
class PoolForm(FlaskForm, metaclass=form_preprocessing):
    form_type = HiddenField("pool")
    id = HiddenField()
    boolean_fields = HiddenField(default="never_update")
    name = StringField()
    description = StringField()
    longitude = FloatField(default=0.0)
    latitude = FloatField(default=0.0)
    operator = SelectField(
        choices=(
            ("all", "Match if all properties match"),
            ("any", "Match if any property matches"),
        )
    )
    never_update = BooleanField("Never update (for manually selected pools)")


class PoolObjectsForm(FlaskForm, metaclass=form_preprocessing):
    form_type = HiddenField("pool_objects")
    list_fields = HiddenField(default="devices,links")
    devices = MultipleObjectField("Device")
    links = MultipleObjectField("Link")


class ImportExportForm(FlaskForm, metaclass=form_preprocessing):
    form_type = HiddenField("import_export")
    boolean_fields = HiddenField(default="replace")
    export_filename = StringField()
    replace = BooleanField()


class OpenNmsForm(FlaskForm, metaclass=form_preprocessing):
    form_type = HiddenField("opennms")
    opennms_rest_api = StringField()
    opennms_devices = StringField()
    node_type = [subtype for subtype in device_subtypes.items()]
    subtype = SelectField(choices=node_type)
    opennms_login = StringField()
    password = PasswordField()


class NetboxForm(FlaskForm, metaclass=form_preprocessing):
    form_type = HiddenField("netbox")
    netbox_address = StringField(default="http://0.0.0.0:8000")
    netbox_token = PasswordField()
    node_type = [subtype for subtype in device_subtypes.items()]
    netbox_type = SelectField(choices=node_type)


class LibreNmsForm(FlaskForm, metaclass=form_preprocessing):
    form_type = HiddenField("librenms")
    librenms_address = StringField(default="http://librenms.example.com")
    node_type = [subtype for subtype in device_subtypes.items()]
    librenms_type = SelectField(choices=node_type)
    librenms_token = PasswordField()


class GoogleEarthForm(FlaskForm, metaclass=form_preprocessing):
    form_type = HiddenField("google_earth")
    name = StringField()
    label_size = IntegerField(default=1)
    line_width = IntegerField(default=2)


class DeviceAutomationForm(FlaskForm, metaclass=form_preprocessing):
    form_type = HiddenField("device_automation")
    list_fields = HiddenField(default="jobs")
    jobs = MultipleObjectField("Job")


class CompareConfigurationsForm(FlaskForm, metaclass=form_preprocessing):
    form_type = HiddenField("configuration")
    display = SelectField(choices=())
    compare_with = SelectField(choices=())


class JobForm(FlaskForm, metaclass=form_preprocessing):
    form_type = HiddenField("job")
    id = HiddenField()
    boolean_fields = HiddenField(
        default=(
            "display_only_failed_nodes,"
            "send_notification,"
            "multiprocessing,"
            "use_workflow_targets,"
            "push_to_git"
        )
    )
    list_fields = HiddenField(default="devices,pools")
    name = StringField()
    description = StringField()
    devices = MultipleObjectField("Device")
    multiprocessing = BooleanField()
    max_processes = IntegerField("Maximum number of processes", default=50)
    credentials = SelectField(
        choices=(("device", "Device Credentials"), ("user", "User Credentials"))
    )
    pools = MultipleObjectField("Pool")
    waiting_time = IntegerField("Waiting time (in seconds)", default=0)
    send_notification = BooleanField()
    send_notification_method = SelectField(
        choices=(
            ("mail_feedback_notification", "Mail"),
            ("slack_feedback_notification", "Slack"),
            ("mattermost_feedback_notification", "Mattermost"),
        )
    )
    display_only_failed_nodes = BooleanField()
    mail_recipient = StringField()
    number_of_retries = IntegerField("Number of retries", default=0)
    time_between_retries = IntegerField("Time between retries (in seconds)", default=10)
    vendor = StringField()
    operating_system = StringField()


class JobFilteringForm(FlaskForm, metaclass=form_preprocessing):
    form_type = HiddenField("job_filtering")
    name = StringField()
    type = StringField()
    description = StringField()
    creator_name = StringField()
    max_processes = StringField()
    credentials = StringField()
    waiting_time = StringField()
    send_notification_method = StringField()
    mail_recipient = StringField()
    number_of_retries = StringField()
    time_between_retries = StringField()


class CompareResultsForm(FlaskForm, metaclass=form_preprocessing):
    form_type = HiddenField("results")
    display = SelectField(choices=())
    compare_with = SelectField(choices=())


class AddJobsForm(FlaskForm, metaclass=form_preprocessing):
    form_type = HiddenField("add_jobs")
    list_fields = HiddenField(default="add_jobs")
    add_jobs = MultipleObjectField("Job")


class WorkflowBuilderForm(FlaskForm, metaclass=form_preprocessing):
    form_type = HiddenField("workflow_builder")
    workflow = ObjectField("Workflow")


def configure_form(cls: FlaskForm) -> FlaskForm:
    cls.properties = ("source_ip", "content")
    for property in ("source_ip", "content"):
        setattr(cls, property, StringField(property))
        setattr(cls, property + "_regex", BooleanField("Regex"))
    return cls


@configure_form
class LogAutomationForm(FlaskForm, metaclass=form_preprocessing):
    form_type = HiddenField("logrule")
    id = HiddenField()
    list_fields = HiddenField(default="jobs")
    name = StringField()
    jobs = MultipleObjectField("Job")


class TaskForm(FlaskForm, metaclass=form_preprocessing):
    form_type = HiddenField("task")
    id = HiddenField()
    boolean_fields = HiddenField(default="is_active")
    is_active = BooleanField()
    name = StringField()
    description = StringField()
    start_date = DateField()
    end_date = DateField()
    frequency = IntegerField()
    frequency_unit = SelectField(
        choices=(
            ("seconds", "Seconds"),
            ("minutes", "Minutes"),
            ("hours", "Hours"),
            ("days", "Days"),
        )
    )
    crontab_expression = StringField()
    job = ObjectField("Job")
    scheduling_mode = SelectField(
        choices=(("standard", "Standard Scheduling"), ("cron", "Crontab Scheduling"))
    )


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
    "service_filtering": JobFilteringForm,
    "task": TaskForm,
    "workflow": JobForm,
}

form_templates = {
    "configuration_filtering": "object_filtering_form",
    "device": "base_form",
    "device_filtering": "object_filtering_form",
    "instance": "base_form",
    "link": "base_form",
    "link_filtering": "object_filtering_form",
    "service_filtering": "filtering_form",
    "task": "base_form",
    "user": "base_form",
}
