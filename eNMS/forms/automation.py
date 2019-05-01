from flask_wtf import FlaskForm
from wtforms import BooleanField, HiddenField, IntegerField, SelectField, StringField

from eNMS.forms import metaform
from eNMS.forms.fields import DateField, MultipleObjectField, ObjectField


class DeviceAutomationForm(FlaskForm, metaclass=metaform):
    form_type = HiddenField(default="device_automation")
    list_fields = HiddenField(default="jobs")
    jobs = MultipleObjectField("Job")


class JobForm(FlaskForm, metaclass=metaform):
    template = "object"
    form_type = HiddenField(default="service,workflow")
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


class ServiceForm(JobForm, metaclass=metaform):
    template = "service"
    form_type = HiddenField(default="service")


class WorkflowForm(JobForm, metaclass=metaform):
    template = "workflow"
    form_type = HiddenField(default="workflow")


class JobFilteringForm(FlaskForm, metaclass=metaform):
    action = "filter"
    form_type = HiddenField(default="job filtering")
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


class CompareResultsForm(FlaskForm, metaclass=metaform):
    form_type = HiddenField(default="results")
    display = SelectField(choices=())
    compare_with = SelectField(choices=())


class AddJobsForm(FlaskForm, metaclass=metaform):
    form_type = HiddenField(default="add_jobs")
    list_fields = HiddenField(default="add_jobs")
    add_jobs = MultipleObjectField("Job")


class WorkflowBuilderForm(FlaskForm, metaclass=metaform):
    form_type = HiddenField(default="workflow_builder")
    workflow = ObjectField("Workflow")


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
    list_fields = HiddenField(default="jobs")
    name = StringField()
    jobs = MultipleObjectField("Job")


class TaskForm(FlaskForm, metaclass=metaform):
    template = "base"
    form_type = HiddenField(default="task")
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
