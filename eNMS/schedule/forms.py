from flask_wtf import FlaskForm
from wtforms import SelectField, TextField


class SchedulingForm(FlaskForm):
    start_date = TextField()
    end_date = TextField()
    name = TextField()
    frequency = TextField()
    job = SelectField()
