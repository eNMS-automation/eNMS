from base.properties import (
    pretty_names,
    node_public_properties,
    link_public_properties
)
from flask_wtf import FlaskForm
from wtforms import IntegerField, SelectField, TextField


class ViewOptionsForm(FlaskForm):
    node_label_choices = [(p, pretty_names[p]) for p in node_public_properties]
    node_label = SelectField('Actions', choices=node_label_choices)
    link_label_choices = [(p, pretty_names[p]) for p in link_public_properties]
    link_label = SelectField('Actions', choices=link_label_choices)


class GoogleEarthForm(FlaskForm):
    name = TextField('Project name')
    label_size = IntegerField('Label size', default=1)
    line_width = IntegerField('Line width', default=2)
