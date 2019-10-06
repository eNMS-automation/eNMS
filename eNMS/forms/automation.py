from ast import parse
from wtforms import (
    BooleanField,
    FloatField,
    HiddenField,
    IntegerField,
    SelectField,
    StringField,
)
from wtforms.widgets import TextArea

from eNMS import app
from eNMS.forms import BaseForm
from eNMS.forms.fields import (
    DictField,
    DictSubstitutionField,
    MultipleInstanceField,
    NoValidationSelectField,
    PasswordSubstitutionField,
    SubstitutionField,
)


class ServiceForm(BaseForm):
    template = "service"
    form_type = HiddenField(default="service")
    id = HiddenField()
    type = StringField("Service Type")
    name = StringField("Name")
    description = StringField("Description")
    device_query = StringField("Device Query")
    device_query_property = SelectField(
        "Query Property Type", choices=(("name", "Name"), ("ip_address", "IP address"))
    )
    devices = MultipleInstanceField("Devices")
    pools = MultipleInstanceField("Pools")
    waiting_time = IntegerField("Waiting time (in seconds)", default=0)
    send_notification = BooleanField("Send a notification")
    send_notification_method = SelectField(
        "Notification Method",
        choices=(
            ("mail_feedback_notification", "Mail"),
            ("slack_feedback_notification", "Slack"),
            ("mattermost_feedback_notification", "Mattermost"),
        ),
    )
    notification_header = StringField(widget=TextArea(), render_kw={"rows": 5})
    include_link_in_summary = BooleanField("Include Result Link in Summary")
    display_only_failed_nodes = BooleanField("Display only Failed Devices")
    mail_recipient = StringField("Mail Recipients (separated by comma)")
    number_of_retries = IntegerField("Number of retries", default=0)
    time_between_retries = IntegerField("Time between retries (in seconds)", default=10)
    maximum_runs = IntegerField("Maximum number of runs", default=1)
    skip = BooleanField("Skip")
    skip_query = StringField("Skip Query (Python)")
    vendor = StringField("Vendor")
    operating_system = StringField("Operating System")
    initial_payload = DictField()
    iteration_values = StringField("Iteration Values (Python Query)")
    iteration_variable_name = StringField(
        "Iteration Variable Name", default="iteration_value"
    )
    iteration_devices = StringField("Iteration Devices (Python Query)")
    iteration_devices_property = SelectField(
        "Iteration Devices Property",
        choices=(("name", "Name"), ("ip_address", "IP address")),
    )
    result_postprocessing = StringField(widget=TextArea(), render_kw={"rows": 7})
    multiprocessing = BooleanField("Multiprocessing")
    max_processes = IntegerField("Maximum number of processes", default=50)
    conversion_method = SelectField(
        choices=(
            ("none", "No conversion"),
            ("text", "Text"),
            ("json", "Json dictionary"),
            ("xml", "XML dictionary"),
        )
    )
    validation_method = SelectField(
        "Validation Method",
        choices=(
            ("none", "No validation"),
            ("text", "Validation by text match"),
            ("dict_included", "Validation by dictionary inclusion"),
            ("dict_equal", "Validation by dictionary equality"),
        ),
    )
    content_match = SubstitutionField(
        "Content Match", widget=TextArea(), render_kw={"rows": 8}
    )
    content_match_regex = BooleanField("Match content with Regular Expression")
    dict_match = DictSubstitutionField("Dictionary to Match Against")
    negative_logic = BooleanField("Negative logic")
    delete_spaces_before_matching = BooleanField("Delete Spaces before Matching")
    query_fields = [
        "device_query",
        "skip_query",
        "iteration_values",
        "result_postprocessing",
    ]

    def validate(self):
        valid_form = super().validate()
        no_recipient_error = (
            self.send_notification.data
            and self.send_notification_method.data == "mail_feedback_notification"
            and not self.mail_recipient.data
            and not app.mail_recipients
        )
        if no_recipient_error:
            self.mail_recipient.errors.append(
                "Please add at least one recipient for the mail notification."
            )
        bracket_error = False
        for query_field in self.query_fields:
            field = getattr(self, query_field)
            try:
                parse(field.data)
            except Exception as exc:
                bracket_error = True
                field.errors.append(f"Wrong python expression ({exc}).")
            if "{{" in field.data and "}}" in field.data:
                bracket_error = True
                field.errors.append(
                    "You cannot use variable substitution "
                    "in a field expecting a python expression."
                )
        conversion_validation_mismatch = (
            self.conversion_method.data == "text"
            and "dict" in self.validation_method.data
            or self.conversion_method.data in ("xml", "json")
            and "dict" not in self.validation_method.data
        )
        if conversion_validation_mismatch:
            self.conversion_method.errors.append(
                f"The conversion method is set to '{self.conversion_method.data}'"
                f" and the validation method to '{self.validation_method.data}' :"
                " these do not match."
            )
        return (
            valid_form
            and not no_recipient_error
            and not bracket_error
            and not conversion_validation_mismatch
        )


class ConnectionForm(ServiceForm):
    form_type = HiddenField(default="connection")
    abstract_service = True
    credentials = SelectField(
        "Credentials",
        choices=(
            ("device", "Device Credentials"),
            ("user", "User Credentials"),
            ("custom", "Custom Credentials"),
        ),
    )
    custom_username = SubstitutionField("Custom Username")
    custom_password = PasswordSubstitutionField("Custom Password")
    start_new_connection = BooleanField("Start New Connection")
    close_connection = BooleanField("Close Connection")
    group = {
        "commands": [
            "credentials",
            "custom_username",
            "custom_password",
            "start_new_connection",
            "close_connection",
        ],
        "default": "expanded",
    }


class NetmikoForm(ConnectionForm):
    form_type = HiddenField(default="netmiko")
    abstract_service = True
    driver = SelectField(choices=app.NETMIKO_DRIVERS)
    use_device_driver = BooleanField(default=True)
    enable_mode = BooleanField(
        "Enable mode (run in enable mode or as root)", default=True
    )
    config_mode = BooleanField("Config mode", default=False)
    fast_cli = BooleanField()
    timeout = IntegerField(default=10)
    delay_factor = FloatField(default=1.0)
    global_delay_factor = FloatField(default=1.0)
    groups = {
        "Netmiko Parameters": {
            "commands": [
                "driver",
                "use_device_driver",
                "enable_mode",
                "config_mode",
                "fast_cli",
                "timeout",
                "delay_factor",
                "global_delay_factor",
            ],
            "default": "expanded",
        },
        "Connection Parameters": ConnectionForm.group,
    }


class NapalmForm(ConnectionForm):
    form_type = HiddenField(default="napalm")
    abstract_service = True
    driver = SelectField(choices=app.NAPALM_DRIVERS)
    use_device_driver = BooleanField(default=True)
    timeout = IntegerField(default=10)
    optional_args = DictField()
    groups = {
        "Napalm Parameters": {
            "commands": ["driver", "use_device_driver", "timeout", "optional_args"],
            "default": "expanded",
        },
        "Connection Parameters": ConnectionForm.group,
    }


class RunForm(BaseForm):
    template = "object"
    form_type = HiddenField(default="run")
    id = HiddenField()


class RestartWorkflowForm(BaseForm):
    action = "restartWorkflow"
    form_type = HiddenField(default="restart_workflow")
    start_services = MultipleInstanceField("Workflow Entry Point(s)")
    restart_runtime = NoValidationSelectField("Restart Runtime", choices=())


class LogsForm(BaseForm):
    template = "logs"
    form_type = HiddenField(default="logs")
    filter = StringField("Filter")
    runtime = NoValidationSelectField("Version", choices=())


class ResultForm(BaseForm):
    template = "result"
    form_type = HiddenField(default="result")


class ConfigurationForm(BaseForm):
    template = "result"
    form_type = HiddenField(default="configuration")


class DisplayForm(BaseForm):
    template = "display"
    form_type = HiddenField(default="display")


class CompareForm(DisplayForm):
    form_type = HiddenField(default="compare")


class DisplayConfigurationForm(DisplayForm):
    form_type = HiddenField(default="display_configuration")


class AddServicesForm(BaseForm):
    action = "addServicesToWorkflow"
    form_type = HiddenField(default="add_services")
    services = MultipleInstanceField("Add services")


class WorkflowLabelForm(BaseForm):
    form_type = HiddenField(default="workflow_label")
    action = "createLabel"
    content = StringField(widget=TextArea(), render_kw={"rows": 15})
    alignment = SelectField(
        "Text Alignment",
        choices=(("center", "Center"), ("left", "Left"), ("right", "Right")),
    )


class WorkflowEdgeForm(BaseForm):
    template = "object"
    form_type = HiddenField(default="workflow_edge")
    id = HiddenField()
    label = StringField()
