from wtforms import HiddenField, SelectField, StringField

from eNMS.base.models import BaseForm


class SchedulingForm(BaseForm):
    id = HiddenField()
    start_date = StringField()
    end_date = StringField()
    name = StringField()
    description = StringField()
    frequency = StringField()
    job = SelectField(choices=())
