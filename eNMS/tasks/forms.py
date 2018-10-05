from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    IntegerField,
    SelectField,
    SelectMultipleField,
    TextField
)


class SchedulingForm(FlaskForm):
    start_date = TextField()
    end_date = TextField()
    name = TextField()
    waiting_time = IntegerField(default=0)
    frequency = TextField()
    run_immediately = BooleanField()
    do_not_run = BooleanField(default=True)
    service_type = SelectField()
    devices = SelectMultipleField(choices=())
    pools = SelectMultipleField(choices=())
    job = SelectField()


class CompareLogsForm(FlaskForm):
    first_version = SelectField(choices=())
    second_version = SelectField(choices=())
    first_device = SelectField(choices=())
    second_device = SelectField(choices=())
