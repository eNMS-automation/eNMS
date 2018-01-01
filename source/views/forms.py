from flask_wtf import FlaskForm
from objects.properties import node_public_properties, link_public_properties
from base.properties import pretty_names
from wtforms import *
from wtforms.validators import optional

def configure_form(cls):
    cls.node_properties = node_public_properties
    cls.link_properties = link_public_properties
    for property in node_public_properties:
        setattr(cls, 'node' + property, TextField(property))
        setattr(cls, 'node' + property + 'regex', BooleanField('Regex'))
    for property in link_public_properties:
        setattr(cls, 'link' + property, TextField(property))
        setattr(cls, 'link' + property + 'regex', BooleanField('Regex'))
    return cls
    
@configure_form
class FilteringForm(FlaskForm):
    node_label_choices = [(p, pretty_names[p]) for p in node_public_properties]
    node_label = SelectField('Actions', choices=node_label_choices)
    link_label_choices = [(p, pretty_names[p]) for p in link_public_properties]
    link_label = SelectField('Actions', choices=link_label_choices)
