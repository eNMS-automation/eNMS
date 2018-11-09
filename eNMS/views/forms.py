from wtforms import IntegerField, StringField

from eNMS.base.models import BaseForm


class GoogleEarthForm(BaseForm):
    name = StringField()
    label_size = IntegerField(default=1)
    line_width = IntegerField(default=2)
