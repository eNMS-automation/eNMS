from flask_wtf import FlaskForm
from objects.properties import node_public_properties, link_public_properties
from wtforms import TextField, BooleanField
from wtforms.validators import optional

def apply_defaults(cls):
    cls.node_public_properties = node_public_properties
    for property in node_public_properties:
        setattr(cls, property, TextField(property))
        setattr(cls, property + 'regex', BooleanField('Regex'))
    return cls
    
@apply_defaults
class NodeFilteringForm(FlaskForm):
    pass