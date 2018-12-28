from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    HiddenField,
    IntegerField,
    StringField,
    SelectField
)

from eNMS.base.models import MultipleObjectField, ObjectField


class JobForm(FlaskForm):
    id = HiddenField()
    boolean_fields = HiddenField(
        default=(
            'send_notification,'
            'multiprocessing,'
            'use_workflow_targets,'
            'push_to_git'
        )
    )
    list_fields = HiddenField(default='devices,pools')
    name = StringField()
    description = StringField()
    devices = MultipleObjectField('Device')
    multiprocessing = BooleanField()
    max_processes = IntegerField('Maximum number of processes', default=50)
    credentials = SelectField(choices=(
        ('device', 'Device Credentials'),
        ('user', 'User Credentials')
    ))
    pools = MultipleObjectField('Pool')
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


class CompareLogsForm(FlaskForm):
    display = SelectField(choices=())
    compare_with = SelectField(choices=())


class AddJobForm(FlaskForm):
    list_fields = HiddenField(default='add_jobs')
    add_jobs = MultipleObjectField('Job')


class WorkflowBuilderForm(FlaskForm):
    workflow = ObjectField('Workflow')
