from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    IntegerField,
    SelectField,
    SelectMultipleField,
    TextField
)


class SchedulingForm(FlaskForm):
    start_date = TextField('Start date')
    end_date = TextField('End date')
    name = TextField('Name')
    waiting_time = IntegerField('Waiting time', default=0)
    frequency = TextField('Frequency')
    run_immediately = BooleanField('Run immediately')
    do_not_run = BooleanField('Do not run', default=True)
    service_type = SelectField('Type of service', choices=())
    devices = SelectMultipleField('', choices=())
    pools = SelectMultipleField('', choices=())
    job = SelectField('', choices=())


class CompareLogsForm(FlaskForm):
    first_version = SelectField('', choices=())
    second_version = SelectField('', choices=())
    first_device = SelectField('', choices=())
    second_device = SelectField('', choices=())
