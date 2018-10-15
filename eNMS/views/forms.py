from flask_wtf import FlaskForm
from wtforms import IntegerField, SelectField, TextField

from eNMS.base.properties import (
    link_public_properties,
    device_public_properties,
    pretty_names
)


class ViewOptionsForm(FlaskForm):
    device_label_choices = [(p, p) for p in device_public_properties]
    device_label = SelectField(choices=device_label_choices)
    link_label_choices = [(p, p) for p in link_public_properties]
    link_label = SelectField(choices=link_label_choices)


class GoogleEarthForm(FlaskForm):
    name = TextField()
    label_size = IntegerField(default=1)
    line_width = IntegerField(default=2)
