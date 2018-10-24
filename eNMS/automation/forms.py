from flask_wtf import FlaskForm
from wtforms import (
    HiddenField,
    IntegerField,
    TextField,
    SelectField,
    SelectMultipleField
)


class ServiceForm(FlaskForm):
    id = HiddenField()
    name = TextField()
    description = TextField()
    devices = SelectMultipleField(choices=())
    pools = SelectMultipleField(choices=())
    waiting_time = IntegerField(default=0)
    number_of_retry = IntegerField(default=1)
    time_between_retries = IntegerField(default=10)


class CompareLogsForm(FlaskForm):
    first_version = SelectField(choices=())
    second_version = SelectField(choices=())


class AddJobForm(FlaskForm):
    job = SelectField()


class WorkflowCreationForm(FlaskForm):
    id = HiddenField()
    name = TextField()
    description = TextField()
    vendor = TextField()
    operating_system = TextField()
    devices = SelectMultipleField(choices=())
    pools = SelectMultipleField(choices=())


class WorkflowBuilderForm(FlaskForm):
    workflow = SelectField()
