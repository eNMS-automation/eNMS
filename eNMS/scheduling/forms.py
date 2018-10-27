from flask_wtf import FlaskForm
from wtforms import HiddenField, SelectField, TextField


class SchedulingForm(FlaskForm):
    id = HiddenField()
    start_date = TextField()
    end_date = TextField()
    name = TextField()
    description = TextField()
    frequency = TextField()
    job = SelectField()
