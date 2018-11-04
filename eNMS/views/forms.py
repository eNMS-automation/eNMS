from wtforms import IntegerField, TextField

from eNMS.base.models import BaseForm


class GoogleEarthForm(BaseForm):
    name = TextField()
    label_size = IntegerField(default=1)
    line_width = IntegerField(default=2)
