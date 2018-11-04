from wtforms import HiddenField, SelectField, TextField

from eNMS.base.models import BaseForm


class SchedulingForm(BaseForm):
    id = HiddenField()
    start_date = TextField()
    end_date = TextField()
    name = TextField()
    description = TextField()
    frequency = TextField()
    job = SelectField()
