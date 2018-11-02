from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    HiddenField,
    IntegerField,
    TextField,
    SelectField,
    SelectMultipleField
)


class JobForm(FlaskForm):
    id = HiddenField()
    name = TextField()
    description = TextField()
    devices = SelectMultipleField(choices=())
    pools = SelectMultipleField(choices=())
    waiting_time = IntegerField('Waiting time (in seconds)', default=0)
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
    vendor = TextField()
    operating_system = TextField()


class CompareLogsForm(FlaskForm):
    first_version = SelectField(choices=())
    second_version = SelectField(choices=())


class AddJobForm(FlaskForm):
    job = SelectField()


class WorkflowForm(JobForm):
    multiprocessing = BooleanField()


class WorkflowBuilderForm(FlaskForm):
    workflow = SelectField()
