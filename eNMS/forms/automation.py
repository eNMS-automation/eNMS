from wtforms import (
    BooleanField,
    HiddenField,
    IntegerField,
    PasswordField,
    SelectField,
    SelectMultipleField,
    StringField,
)
from wtforms.widgets import TextArea

from eNMS.controller import controller
from eNMS.forms import BaseForm
from eNMS.forms.fields import (
    DictField,
    MultipleInstanceField,
    NoValidationSelectField,
    NoValidationSelectMultipleField,
    PasswordSubstitutionField,
    SubstitutionField,
)


class DeviceAutomationForm(BaseForm):
    template = "device_automation"
    form_type = HiddenField(default="device_automation")
    jobs = MultipleInstanceField("Jobs", instance_type="Job")


class JobForm(BaseForm):
    template = "object"
    form_type = HiddenField(default="job")
    id = HiddenField()
    type = StringField("Service Type")
    name = StringField("Name")
    description = StringField("Description")
    yaql_query = SubstitutionField("YaQL Query")
    query_property_type = SelectField(
        "Query Property Type", choices=(("name", "Name"), ("ip_address", "IP address"))
    )
    devices = MultipleInstanceField("Devices", instance_type="Device")
    pools = MultipleInstanceField("Pools", instance_type="Pool")
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
    start_new_connection = BooleanField("Start New Connection")
    vendor = StringField("Vendor")
    operating_system = StringField("Operating System")
    shape = SelectField(
        "Shape",
        choices=(
            ("box", "Box"),
            ("circle", "Circle"),
            ("square", "Square"),
            ("diamond", "Diamond"),
            ("triangle", "Triangle"),
            ("ellipse", "Ellipse"),
            ("database", "Database"),
        ),
    )
    size = IntegerField("Size", default=40)
    color = StringField("Color", default="#D2E5FF")
    initial_payload = DictField()

    def validate(self) -> bool:
        valid_form = super().validate()
        no_recipient_error = (
            self.send_notification.data
            and self.send_notification_method.data == "mail_feedback_notification"
            and not self.mail_recipient.data
            and not controller.mail_recipients
        )
        if no_recipient_error:
            self.mail_recipient.errors.append(
                "Please add at least one recipient for the mail notification."
            )
        return valid_form and not no_recipient_error


class ServiceForm(JobForm):
    template = "service"
    form_type = HiddenField(default="service")
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
    multiprocessing = BooleanField("Multiprocessing")
    max_processes = IntegerField("Maximum number of processes", default=50)


class WorkflowForm(JobForm):
    template = "workflow"
    form_type = HiddenField(default="workflow")
    use_workflow_targets = BooleanField("Use Workflow Targets")


class ResultsForm(BaseForm):
    template = "results"
    compare = BooleanField(default=False)
    view_type = SelectField(
        "View", choices=(("text", "Display as text"), ("json", "Display as JSON"), ("compare", "Compare both versions"))
    )
    timestamp = NoValidationSelectField("Version", choices=())
    timestamp_compare = NoValidationSelectField("Version", choices=())


class ServiceResultsForm(ResultsForm):
    form_type = HiddenField(default="service_results")
    success_type = SelectField(
        "View", choices=(("all", "All results"), ("success", "Successful results"), ("failure", "Failed results"))
    )
    device = NoValidationSelectField(
        "Device", choices=(("global", "Global Result"), ("all", "All devices"))
    )
    device_compare = NoValidationSelectField(
        "Device", choices=(("global", "Global Result"), ("all", "All devices"))
    )


class WorkflowResultsForm(ResultsForm):
    form_type = HiddenField(default="workflow_results")
    success_type = SelectField(
        "View", choices=(("all", "All results"), ("success", "Successful results"), ("failure", "Failed results"))
    )
    device = NoValidationSelectField(
        "Device", choices=(("global", "Global Result"), ("all", "All devices"))
    )
    device_compare = NoValidationSelectField(
        "Device", choices=(("global", "Global Result"), ("all", "All devices"))
    )
    job = NoValidationSelectField(
        "Job", choices=(("global", "Global Result"), ("all", "All jobs"))
    )
    job_compare = NoValidationSelectField(
        "Job", choices=(("global", "Global Result"), ("all", "All jobs"))
    )


class DeviceResultsForm(BaseForm):
    form_type = HiddenField(default="device_results")
    job = NoValidationSelectField(
        "Job", choices=(("global", "Global Result"), ("all", "All jobs"))
    )
    job_compare = NoValidationSelectField(
        "Job", choices=(("global", "Global Result"), ("all", "All jobs"))
    )


class RestartWorkflowForm(BaseForm):
    action = "restartWorkflow"
    form_type = HiddenField(default="restart_workflow")
    payload_version = NoValidationSelectField("Payload Version", choices=())
    payloads_to_include = NoValidationSelectMultipleField(
        "Payloads to Include", choices=()
    )
    start_points = NoValidationSelectMultipleField("Start Points", choices=())


class AddJobsForm(BaseForm):
    template = "base"
    action = "addJobsToWorkflow"
    form_type = HiddenField(default="add_jobs")
    jobs = MultipleInstanceField("Add jobs", instance_type="Job")


class ServiceTableForm(BaseForm):
    form_type = HiddenField(default="service_table")
    services = SelectField(choices=())
