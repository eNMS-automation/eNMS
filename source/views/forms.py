from base.properties import pretty_names
from flask_wtf import FlaskForm
from objects.properties import node_public_properties, link_public_properties
from wtforms import *

class ViewOptionsForm(FlaskForm):
    node_label_choices = [(p, pretty_names[p]) for p in node_public_properties]
    node_label = SelectField('Actions', choices=node_label_choices)
    link_label_choices = [(p, pretty_names[p]) for p in link_public_properties]
    link_label = SelectField('Actions', choices=link_label_choices)