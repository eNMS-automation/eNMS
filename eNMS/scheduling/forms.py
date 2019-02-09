from flask_wtf import FlaskForm
from wtforms import HiddenField, IntegerField, StringField

from eNMS.base.models import ObjectField


class SchedulingForm(FlaskForm):
    id = HiddenField()
    start_date = StringField()
    end_date = StringField()
    name = StringField()
    description = StringField()
    frequency = IntegerField()
    job = ObjectField('Job')
