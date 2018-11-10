from wtforms import (
    BooleanField,
    HiddenField,
    IntegerField,
    StringField,
    SelectField,
    SelectMultipleField
)

from eNMS.base.models import BaseForm


class JobForm(BaseForm):
    id = HiddenField()
    name = StringField()
    description = StringField()
    devices = SelectMultipleField(choices=())
    pools = SelectMultipleField(choices=())
    waiting_time = IntegerField('Waiting time (in seconds)', default=0)
    send_notification = BooleanField()
    send_notification_method = SelectField(choices=(
        ('mail_feedback_notification', 'Mail'),
        ('slack_feedback_notification', 'Slack'),
        ('mattermost_feedback_notification', 'Mattermost'),
    ))
    number_of_retries = IntegerField('Number of retries', default=0)
    time_between_retries = IntegerField(
        'Time between retries (in seconds)',
        default=10
    )
    vendor = StringField()
    operating_system = StringField()


class CompareLogsForm(BaseForm):
    display = SelectField(choices=())
    compare_with = SelectField(choices=())


class AddJobForm(BaseForm):
    job = SelectField()


class WorkflowForm(JobForm):
    multiprocessing = BooleanField()


class WorkflowBuilderForm(BaseForm):
    workflow = SelectField()
