from ast import parse
from wtforms import BooleanField, HiddenField, IntegerField, SelectField, StringField
from wtforms.widgets import TextArea

from eNMS import app
from eNMS.forms import BaseForm
from eNMS.forms.fields import (
    DictField,
    MultipleInstanceField,
    NoValidationSelectField,
    PasswordSubstitutionField,
    SubstitutionField,
)


class JobForm(BaseForm):
    template = "job"
    form_type = HiddenField(default="job")
    id = HiddenField()
    type = StringField("Service Type")
    name = StringField("Name")
    description = StringField("Description")
    python_query = StringField("Python Query")
    query_property_type = SelectField(
        "Query Property Type", choices=(("name", "Name"), ("ip_address", "IP address"))
    )
    devices = MultipleInstanceField("Devices", instance_type="device")
    pools = MultipleInstanceField("Pools", instance_type="pool")
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
    start_new_connection = BooleanField("Start New Connection")
    skip = BooleanField("Skip")
    skip_python_query = StringField("Skip (Python Query)")
    vendor = StringField("Vendor")
    operating_system = StringField("Operating System")
    initial_payload = DictField()
    iteration_values = StringField("Iteration Targets (Python Query)")
    iteration_variable_name = StringField(
        "Iteration Variable Name", default="iteration_value"
    )
    result_postprocessing = StringField(widget=TextArea(), render_kw={"rows": 7})
    query_fields = ["python_query", "skip_python_query", "iteration_values"]

    def validate(self) -> bool:
        valid_form = super().validate()
        no_recipient_error = (
            self.send_notification.data
            and self.send_notification_method.data == "mail_feedback_notification"
            and not self.mail_recipient.data
            and not app.mail_recipients
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
        if no_recipient_error:
            self.mail_recipient.errors.append(
                "Please add at least one recipient for the mail notification."
            )
        return valid_form and not no_recipient_error and not bracket_error


class RunForm(BaseForm):
    template = "object"
    form_type = HiddenField(default="run")
    id = HiddenField()


class ServiceForm(JobForm):
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
    form_type = HiddenField(default="workflow")
    use_workflow_devices = BooleanField("Use Workflow Devices", default=True)
    traversal_mode = SelectField(
        "Traversal Mode",
        choices=(
            ("service", "Workflow runs one service at a time"),
            ("device", "All devices run independently through the workflow"),
        ),
    )
    start_jobs = MultipleInstanceField("Workflow Entry Point(s)", instance_type="job")
    restart_runtime = NoValidationSelectField("Restart Runtime", choices=())


class RestartWorkflowForm(BaseForm):
    action = "restartWorkflow"
    form_type = HiddenField(default="restart_workflow")
    start_jobs = MultipleInstanceField("Workflow Entry Point(s)", instance_type="job")
    restart_runtime = NoValidationSelectField("Restart Runtime", choices=())


class LogsForm(BaseForm):
    template = "logs"
    form_type = HiddenField(default="logs")
    filter = StringField("Filter")
    runtime = NoValidationSelectField("Version", choices=())


class ResultForm(BaseForm):
    template = "result"
    form_type = HiddenField(default="result")


class DisplayResultForm(BaseForm):
    template = "display_result"
    form_type = HiddenField(default="display_result")
    view_type = SelectField(
        "View", choices=(("view", "Display as JSON"), ("text", "Display as text"))
    )


class AddJobsForm(BaseForm):
    action = "addJobsToWorkflow"
    form_type = HiddenField(default="add_jobs")
    jobs = MultipleInstanceField("Add jobs", instance_type="job")


class ServiceTableForm(BaseForm):
    form_type = HiddenField(default="service_table")
    services = SelectField(choices=())


class WorkflowLabelForm(BaseForm):
    form_type = HiddenField(default="workflow_label")
    action = "createLabel"
    content = StringField(widget=TextArea(), render_kw={"rows": 15})


class WorkflowEdgeForm(BaseForm):
    template = "object"
    form_type = HiddenField(default="workflow_edge")
    id = HiddenField()
    label = StringField()
