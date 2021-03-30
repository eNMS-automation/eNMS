from wtforms.validators import InputRequired
from wtforms.widgets import TextArea

from eNMS import app
from eNMS.forms import BaseForm
from eNMS.forms.fields import (
    BooleanField,
    DictField,
    FloatField,
    HiddenField,
    InstanceField,
    IntegerField,
    MultipleInstanceField,
    PasswordField,
    SelectField,
    StringField,
)


class ServiceForm(BaseForm):
    template = "service"
    form_type = HiddenField(default="service")
    get_request_allowed = False
    id = HiddenField()
    name = StringField("Name")
    type = StringField("Service Type")
    access_groups = StringField("Groups")
    shared = BooleanField("Shared")
    scoped_name = StringField("Scoped Name", [InputRequired()])
    description = StringField("Description")
    device_query = StringField(
        "Device Query", python=True, widget=TextArea(), render_kw={"rows": 2}
    )
    device_query_property = SelectField(
        "Query Property Type", choices=(("name", "Name"), ("ip_address", "IP address"))
    )
    target_devices = MultipleInstanceField("Devices")
    disable_result_creation = BooleanField("Save only failed results")
    target_pools = MultipleInstanceField("Pools")
    update_target_pools = BooleanField("Update target pools before running")
    update_pools_after_running = BooleanField("Update pools after running")
    workflows = MultipleInstanceField("Workflows")
    waiting_time = IntegerField(
        "Time to Wait before next service is started (in seconds)", default=0
    )
    priority = IntegerField("Priority", default=1)
    send_notification = BooleanField("Send a notification")
    send_notification_method = SelectField(
        "Notification Method",
        choices=(("mail", "Mail"), ("slack", "Slack"), ("mattermost", "Mattermost")),
    )
    notification_header = StringField(widget=TextArea(), render_kw={"rows": 5})
    include_device_results = BooleanField("Include Device Results")
    include_link_in_summary = BooleanField("Include Result Link in Summary")
    display_only_failed_nodes = BooleanField("Display only Failed Devices")
    mail_recipient = StringField("Mail Recipients (separated by comma)")
    reply_to = StringField("Reply-to Email Address")
    number_of_retries = IntegerField("Number of retries", default=0)
    time_between_retries = IntegerField("Time between retries (in seconds)", default=10)
    max_number_of_retries = IntegerField("Maximum number of retries", default=100)
    credential_type = SelectField(
        "Type of Credentials",
        choices=(
            ("any", "Any"),
            ("read-write", "Read Write"),
            ("read-only", "Read Only"),
        ),
    )
    maximum_runs = IntegerField("Maximum number of runs", default=1)
    skip_query = StringField(
        "Skip Query (Python)", python=True, widget=TextArea(), render_kw={"rows": 2}
    )
    skip_value = SelectField(
        "Skip Value",
        choices=(
            ("success", "Success"),
            ("failure", "Failure"),
            ("discard", "Discard"),
        ),
    )
    vendor = StringField("Vendor")
    operating_system = StringField("Operating System")
    iteration_values = StringField("Iteration Values", python=True)
    initial_payload = DictField()
    iteration_variable_name = StringField(
        "Iteration Variable Name", default="iteration_value"
    )
    iteration_devices = StringField("Iteration Devices", python=True)
    iteration_devices_property = SelectField(
        "Iteration Devices Property",
        choices=(("name", "Name"), ("ip_address", "IP address")),
    )
    preprocessing = StringField(type="code", python=True, widget=TextArea())
    postprocessing = StringField(type="code", python=True, widget=TextArea())
    postprocessing_mode = SelectField(
        choices=(
            ("always", "Always run"),
            ("success", "Run on success only"),
            ("failure", "Run on failure only"),
        )
    )
    default_access = SelectField(
        choices=(
            ("creator", "Creator only"),
            ("public", "Public (all users)"),
            ("admin", "Admin Users only"),
        )
    )
    log_level = SelectField(
        "Logging",
        choices=((0, "Disable logging"), *enumerate(app.log_levels, 1)),
        default=1,
    )
    multiprocessing = BooleanField("Multiprocessing")
    max_processes = IntegerField("Maximum number of processes", default=15)
    validation_condition = SelectField(
        choices=(
            ("none", "No validation"),
            ("success", "Run on success only"),
            ("failure", "Run on failure only"),
            ("always", "Always run"),
        )
    )
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
            ("text", "Validation by text match"),
            ("dict_included", "Validation by dictionary inclusion"),
            ("dict_equal", "Validation by dictionary equality"),
        ),
    )
    content_match = StringField(
        "Content Match", widget=TextArea(), render_kw={"rows": 8}, substitution=True
    )
    content_match_regex = BooleanField('"Content Match" is a regular expression')
    dict_match = DictField("Dictionary to Match Against", substitution=True)
    negative_logic = BooleanField("Negative logic")
    delete_spaces_before_matching = BooleanField("Delete Spaces before Matching")
    run_method = SelectField(
        "Run Method",
        choices=(
            ("per_device", "Run the service once per device"),
            ("once", "Run the service once"),
        ),
    )

    def validate(self):
        valid_form = super().validate()
        no_recipient_error = (
            self.send_notification.data
            and self.send_notification_method.data == "mail"
            and not self.mail_recipient.data
        )
        if no_recipient_error:
            self.mail_recipient.errors.append(
                "Please add at least one recipient for the mail notification."
            )
        forbidden_name_error = self.scoped_name.data in ("Start", "End", "Placeholder")
        if forbidden_name_error:
            self.name.errors.append("This name is not allowed.")
        conversion_validation_mismatch = self.validation_condition.data != "none" and (
            self.conversion_method.data == "text"
            and "dict" in self.validation_method.data
            or self.conversion_method.data in ("xml", "json")
            and "dict" not in self.validation_method.data
        )
        if conversion_validation_mismatch:
            self.conversion_method.errors.append(
                f"The conversion method is set to {self.conversion_method.data}"
                f" and the validation method to {self.validation_method.data} :"
                " these do not match."
            )
        empty_validation = self.validation_condition.data != "none" and (
            self.validation_method.data == "text"
            and not self.content_match.data
            or self.validation_method.data == "dict_included"
            and self.dict_match.data == "{}"
        )
        if empty_validation:
            self.content_match.errors.append(
                f"The validation method is set to '{self.validation_method.data}'"
                f" and the matching value is empty: these do no match."
            )
        too_many_threads_error = (
            self.max_processes.data > app.settings["automation"]["max_process"]
        )
        if too_many_threads_error:
            self.max_processes.errors.append(
                "The number of threads used for multiprocessing must be "
                f"less than {app.settings['automation']['max_process']}."
            )
        shared_service_error = not self.shared.data and len(self.workflows.data) > 1
        if shared_service_error:
            self.shared.errors.append(
                "The 'shared' property is unticked, but the service belongs"
                " to more than one workflow: this is incompatible."
            )
        return (
            valid_form
            and not conversion_validation_mismatch
            and not empty_validation
            and not forbidden_name_error
            and not no_recipient_error
            and not shared_service_error
            and not too_many_threads_error
        )


class ConnectionForm(ServiceForm):
    form_type = HiddenField(default="connection")
    get_request_allowed = False
    abstract_service = True
    credentials = SelectField(
        "Credentials",
        choices=(
            ("device", "Device Credentials"),
            ("user", "User Credentials"),
            ("custom", "Custom Credentials"),
        ),
    )
    custom_username = StringField("Custom Username", substitution=True)
    custom_password = PasswordField("Custom Password", substitution=True)
    start_new_connection = BooleanField("Start New Connection")
    close_connection = BooleanField("Close Connection")
    groups = {
        "Connection Parameters": {
            "commands": [
                "credentials",
                "custom_username",
                "custom_password",
                "start_new_connection",
                "close_connection",
            ],
            "default": "expanded",
        }
    }


class NetmikoForm(ConnectionForm):
    form_type = HiddenField(default="netmiko")
    abstract_service = True
    driver = SelectField(choices=app.netmiko_drivers)
    use_device_driver = BooleanField(default=True)
    enable_mode = BooleanField(
        "Enable mode (run in enable mode or as root)", default=True
    )
    config_mode = BooleanField("Config mode", default=False)
    fast_cli = BooleanField()
    timeout = FloatField(default=10.0)
    delay_factor = FloatField(
        (
            "Delay Factor (Changing from default of 1"
            " will nullify Netmiko Timeout setting)"
        ),
        default=1.0,
    )
    global_delay_factor = FloatField(
        (
            "Global Delay Factor (Changing from default of 1"
            " will nullify Netmiko Timeout setting)"
        ),
        default=1.0,
    )
    jump_on_connect = BooleanField(
        "Jump to remote device on connect",
        default=False,
        help="netmiko/jump_on_connect",
    )
    jump_command = StringField(
        label="Command that jumps to device",
        default="ssh jump_server_IP",
        substitution=True,
        help="netmiko/jump_command",
    )
    jump_username = StringField(
        label="Device username", substitution=True, help="netmiko/jump_username"
    )
    jump_password = PasswordField(
        label="Device password", substitution=True, help="netmiko/jump_password"
    )
    exit_command = StringField(
        label="Command to exit device back to original device",
        default="exit",
        substitution=True,
        help="netmiko/exit_command",
    )
    expect_username_prompt = StringField(
        "Expected username prompt",
        default="username:",
        substitution=True,
        help="netmiko/expect_username_prompt",
    )
    expect_password_prompt = StringField(
        "Expected password prompt",
        default="password",
        substitution=True,
        help="netmiko/expect_password_prompt",
    )
    expect_prompt = StringField(
        "Expected prompt after login",
        default="admin.*$",
        substitution=True,
        help="netmiko/expect_prompt",
    )
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
        **ConnectionForm.groups,
        "Jump on connect Parameters": {
            "commands": [
                "jump_on_connect",
                "jump_command",
                "expect_username_prompt",
                "jump_username",
                "expect_password_prompt",
                "jump_password",
                "expect_prompt",
                "exit_command",
            ],
            "default": "hidden",
        },
    }


class NapalmForm(ConnectionForm):
    form_type = HiddenField(default="napalm")
    get_request_allowed = False
    abstract_service = True
    driver = SelectField(choices=app.napalm_drivers)
    use_device_driver = BooleanField(default=True)
    timeout = IntegerField(default=10)
    optional_args = DictField()
    groups = {
        "Napalm Parameters": {
            "commands": ["driver", "use_device_driver", "timeout", "optional_args"],
            "default": "expanded",
        },
        **ConnectionForm.groups,
    }


class RestartWorkflowForm(BaseForm):
    action = "eNMS.workflow.restartWorkflow"
    form_type = HiddenField(default="restart_workflow")
    start_services = HiddenField()
    restart_runtime = SelectField("Restart Runtime", validate_choice=False)


class FileForm(BaseForm):
    template = "file"
    form_type = HiddenField(default="file")
    file_content = StringField(widget=TextArea(), render_kw={"rows": 8})


class AddServiceForm(BaseForm):
    form_type = HiddenField(default="add_services_to_workflow")
    template = "add_services_to_workflow"
    mode = SelectField(
        "Mode",
        choices=(
            ("deep", "Deep Copy (creates a duplicate from the service)"),
            ("shallow", "Shallow Copy (creates a reference to the service)"),
        ),
    )
    search = StringField()


class RunServiceForm(BaseForm):
    action = "eNMS.automation.runServicesOnTargets"
    button_label = "Run Service"
    button_class = "primary"
    form_type = HiddenField(default="run_service")
    targets = HiddenField()
    type = HiddenField()
    service = InstanceField("Services", model="service")


class WorkflowLabelForm(BaseForm):
    form_type = HiddenField(default="workflow_label")
    action = "eNMS.workflow.createLabel"
    text = StringField(widget=TextArea(), render_kw={"rows": 15})
    alignment = SelectField(
        "Text Alignment",
        choices=(("left", "Left"), ("center", "Center"), ("right", "Right")),
    )


class WorkflowEdgeForm(BaseForm):
    action = "eNMS.base.processData"
    form_type = HiddenField(default="workflow_edge")
    id = HiddenField()
    label = StringField()
    color = StringField()
