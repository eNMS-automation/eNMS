from flask_wtf import FlaskForm
from wtforms import BooleanField, SelectField, TextField


class SchedulingForm(FlaskForm):
    start_date = TextField()
    end_date = TextField()
    name = TextField()
    frequency = TextField()
    service_type = SelectField()
    job = SelectField()
