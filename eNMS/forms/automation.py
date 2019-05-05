from flask_wtf import FlaskForm
from wtforms import BooleanField, HiddenField, IntegerField, SelectField, StringField

from eNMS.forms import metaform
from eNMS.forms.fields import DateField, MultipleInstanceField, InstanceField


class DeviceAutomationForm(FlaskForm, metaclass=metaform):
    form_type = HiddenField(default="device_automation")
    jobs = MultipleInstanceField("Jobs", instance_type="Job")


class JobForm(FlaskForm, metaclass=metaform):
    template = "object"
    form_type = HiddenField(default="job")
    id = HiddenField()
    type = StringField("Service Type")
    name = StringField("Name")
    description = StringField("Description")
    devices = MultipleInstanceField("Devices", instance_type="Device")
    multiprocessing = BooleanField("Multiprocessing")
    max_processes = IntegerField("Maximum number of processes", default=50)
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
    display_only_failed_nodes = BooleanField("Display only Failed Devices")
    mail_recipient = StringField("Mail Recipients (separated by comma)")
    number_of_retries = IntegerField("Number of retries", default=0)
    time_between_retries = IntegerField("Time between retries (in seconds)", default=10)
    vendor = StringField("Vendor")
    operating_system = StringField("Operating System")


class ServiceForm(JobForm, metaclass=metaform):
    template = "service"
    form_type = HiddenField(default="service")


class WorkflowForm(JobForm, metaclass=metaform):
    template = "workflow"
    form_type = HiddenField(default="workflow")


class JobFilteringForm(FlaskForm, metaclass=metaform):
    action = "filter"
    form_type = HiddenField(default="job filtering")
    name = StringField("Name")
    type = StringField("Service Type")
    description = StringField("Description")
    creator = StringField("Creator")
    max_processes = StringField("Maximum number of processes")
    credentials = StringField("Credentials")
    waiting_time = StringField("Waiting Time")
    send_notification_method = StringField("Notification Method")
    mail_recipient = StringField("Mail Recipient")
    number_of_retries = StringField("Number of retries")
    time_between_retries = StringField("Time between retries (in seconds)")


class CompareResultsForm(FlaskForm, metaclass=metaform):
    template = "results"
    form_type = HiddenField(default="results")
    display = SelectField("Version to display", choices=())
    compare_with = SelectField("Compare against", choices=())


class AddJobsForm(FlaskForm, metaclass=metaform):
    form_type = HiddenField(default="add_jobs")
    add_jobs = MultipleInstanceField("Add jobs", instance_type="Job")


class WorkflowBuilderForm(FlaskForm, metaclass=metaform):
    form_type = HiddenField(default="workflow_builder")
    workflow = InstanceField("Workflow", instance_type="Workflow")


def configure_form(cls: FlaskForm) -> FlaskForm:
    cls.properties = ("source_ip", "content")
    for property in ("source_ip", "content"):
        setattr(cls, property, StringField(property))
        setattr(cls, property + "_regex", BooleanField("Regex"))
    return cls


@configure_form
class LogAutomationForm(FlaskForm, metaclass=metaform):
    form_type = HiddenField(default="logrule")
    id = HiddenField()
    name = StringField()
    jobs = MultipleInstanceField("Jobs", instance_type="Job")


class TaskForm(FlaskForm, metaclass=metaform):
    template = "base"
    form_type = HiddenField(default="task")
    id = HiddenField()
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
    job = InstanceField("Job", instance_type="Job")
    scheduling_mode = SelectField(
        choices=(("standard", "Standard Scheduling"), ("cron", "Crontab Scheduling"))
    )
