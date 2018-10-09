from flask_wtf import FlaskForm
from wtforms import SelectField


class CompareLogsForm(FlaskForm):
    first_version = SelectField(choices=())
    second_version = SelectField(choices=())
