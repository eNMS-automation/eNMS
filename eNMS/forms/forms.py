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


class DeviceAutomationForm(FlaskForm, metaclass=metaform):
    form_type = HiddenField(default="device_automation")
    list_fields = HiddenField(default="jobs")
    jobs = MultipleObjectField("Job")


class CompareConfigurationsForm(FlaskForm, metaclass=metaform):
    form_type = HiddenField(default="configuration")
    display = SelectField(choices=())
    compare_with = SelectField(choices=())


class JobForm(FlaskForm, metaclass=metaform):
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
    form_type = HiddenField(default="service")


class WorkflowForm(JobForm, metaclass=metaform):
    form_type = HiddenField(default="workflow")


class JobFilteringForm(FlaskForm, metaclass=metaform):
    form_type = HiddenField(default="job_filtering")
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


class LogFilteringForm(FlaskForm):
    form_type = HiddenField(default="log_filtering")
    source_ip_address = StringField()
    content = StringField()


@configure_form
class LogAutomationForm(FlaskForm, metaclass=metaform):
    form_type = HiddenField(default="logrule")
    id = HiddenField()
    list_fields = HiddenField(default="jobs")
    name = StringField()
    jobs = MultipleObjectField("Job")


class TaskForm(FlaskForm, metaclass=metaform):
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
    "log_filtering": LogFilteringForm,
    "logrule": LogAutomationForm,
    "pool": PoolForm,
    "pool_objects": PoolObjectsForm,
    "results": CompareResultsForm,
    "service": JobForm,
    "service_filtering": JobFilteringForm,
    "task": TaskForm,
    "user": UserForm,
    "user_filtering": UserFilteringForm,
    "workflow": JobForm,
}

form_templates = {
    "configuration_filtering": "filtering_form",
    "device": "base_form",
    "device_filtering": "filtering_form",
    "instance": "base_form",
    "link": "base_form",
    "link_filtering": "filtering_form",
    "log_filtering": "filtering_form",
    "service_filtering": "filtering_form",
    "task": "base_form",
    "user": "base_form",
    "user_filtering": "filtering_form",
}
