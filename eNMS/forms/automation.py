from wtforms import BooleanField, HiddenField, IntegerField, SelectField, StringField
from wtforms.widgets import TextArea

from eNMS.controller import controller
from eNMS.forms import BaseForm
from eNMS.forms.fields import DateField, DictField, MultipleInstanceField, InstanceField


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
    define_devices_from_payload = BooleanField("Define Devices from Payload")
    yaql_query = StringField("YaQL Query")
    query_property_type = SelectField(
        "Query Property Type", choices=(("name", "Name"), ("ip_address", "IP address"))
    )
    devices = MultipleInstanceField("Devices", instance_type="Device")
    credentials = SelectField(
        "Credentials",
        choices=(("device", "Device Credentials"), ("user", "User Credentials")),
    )
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
    display_only_failed_nodes = BooleanField("Display only Failed Devices")
    mail_recipient = StringField("Mail Recipients (separated by comma)")
    number_of_retries = IntegerField("Number of retries", default=0)
    time_between_retries = IntegerField("Time between retries (in seconds)", default=10)
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
    size = IntegerField("Size")
    color = StringField("Color")

    def validate(self) -> bool:
        if not super().validate():
            return False
        if (
            self.send_notification.data
            and self.send_notification_method.data == "mail_feedback_notification"
            and not self.mail_recipient.data
            and not controller.mail_recipients
        ):
            self.mail_recipient.errors.append(
                "Please add at least one recipient" " for the mail notification."
            )
            return False
        return True


class ServiceForm(JobForm):
    template = "service"
    form_type = HiddenField(default="service")
    multiprocessing = BooleanField("Multiprocessing")
    max_processes = IntegerField("Maximum number of processes", default=50)


class WorkflowForm(JobForm):
    template = "workflow"
    form_type = HiddenField(default="workflow")
    use_workflow_targets = BooleanField("Use Workflow Targets")


class CompareResultsForm(BaseForm):
    template = "results"
    form_type = HiddenField(default="results")
    display = SelectField("Version to display", choices=())
    compare_with = SelectField("Compare Against", choices=())


class RestartWorkflowForm(BaseForm):
    template = "restart_workflow"
    action = "restartWorkflow"
    form_type = HiddenField(default="restart_workflow")
    payload_version = SelectField("Payload Version", choices=())


class AddJobsForm(BaseForm):
    template = "base"
    action = "addJobsToWorkflow"
    form_type = HiddenField(default="add_jobs")
    jobs = MultipleInstanceField("Add jobs", instance_type="Job")


class ServiceTableForm(BaseForm):
    form_type = HiddenField(default="service_table")
    services = SelectField(choices=())


def configure_form(cls: BaseForm) -> BaseForm:
    cls.properties = ("origin", "name")
    for property in ("origin", "name"):
        setattr(cls, property, StringField(property))
        setattr(cls, property + "_regex", BooleanField("Regex"))
    return cls


@configure_form
class EventForm(BaseForm):
    template = "event"
    form_type = HiddenField(default="event")
    id = HiddenField()
    name = StringField("Name")
    jobs = MultipleInstanceField("Jobs", instance_type="Job")


class TaskForm(BaseForm):
    template = "object"
    form_type = HiddenField(default="task")
    id = HiddenField()
    is_active = BooleanField("Is Active")
    name = StringField("Name")
    description = StringField("Description")
    start_date = DateField("Start Date")
    end_date = DateField("End Date")
    frequency = IntegerField("Frequency", default=0)
    frequency_unit = SelectField(
        "Frequency Unit",
        choices=(
            ("seconds", "Seconds"),
            ("minutes", "Minutes"),
            ("hours", "Hours"),
            ("days", "Days"),
        ),
    )
    crontab_expression = StringField("Crontab Expression")
    job = InstanceField("Job", instance_type="Job")
    scheduling_mode = SelectField(
        "Scheduling Mode",
        choices=(("standard", "Standard Scheduling"), ("cron", "Crontab Scheduling")),
    )
    devices = MultipleInstanceField("Devices", instance_type="Device")
    pools = MultipleInstanceField("Pools", instance_type="Pool")
    payload = DictField("Payload")
