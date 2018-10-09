from flask_wtf import FlaskForm
from wtforms import TextField, SelectField, SelectMultipleField


class ServiceForm(FlaskForm):
    name = TextField()
    description = TextField()
    devices = SelectMultipleField(choices=())
    pools = SelectMultipleField(choices=())


class CompareLogsForm(FlaskForm):
    first_version = SelectField(choices=())
    second_version = SelectField(choices=())
