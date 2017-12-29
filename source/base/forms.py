from flask_wtf import FlaskForm
from wtforms import *
from objects.properties import *
from .properties import pretty_names

class DiagramPropertiesForm(FlaskForm):
    node_choices = [(p, pretty_names[p]) for p in node_diagram_properties]
    node_properties = SelectMultipleField('Node properties', choices=node_choices)
    link_choices = [(p, pretty_names[p]) for p in link_diagram_properties]
    link_properties = SelectMultipleField('Link properties', choices=link_choices)
