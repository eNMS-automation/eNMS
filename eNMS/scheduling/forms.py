from flask_wtf import FlaskForm
from wtforms import HiddenField, SelectField, StringField


class SchedulingForm(FlaskForm):
    id = HiddenField()
    start_date = StringField()
    end_date = StringField()
    name = StringField()
    description = StringField()
    frequency = StringField()
    job = SelectField(choices=())
