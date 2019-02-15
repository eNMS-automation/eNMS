from flask_wtf import FlaskForm
from wtforms import BooleanField, HiddenField, IntegerField, StringField

from eNMS.base.models import ObjectField


class SchedulingForm(FlaskForm):
    id = HiddenField()
    boolean_fields = HiddenField(default="is_active")
    is_active = BooleanField()
    start_date = StringField()
    end_date = StringField()
    name = StringField()
    description = StringField()
    frequency = IntegerField()
    job = ObjectField("Job")
