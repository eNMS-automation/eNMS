from flask_wtf import FlaskForm
from wtforms import SelectField, TextField


class SchedulingForm(FlaskForm):
    task_start_date = TextField()
    task_end_date = TextField()
    task_name = TextField()
    task_frequency = TextField()
    task_job = SelectField()
