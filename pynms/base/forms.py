from flask_wtf import FlaskForm
from wtforms import *
from objects.properties import *
from .properties import pretty_names

## Login and registration

class LoginForm(FlaskForm):
    username = TextField('Username')
    password = PasswordField('Password')
    
class CreateAccountForm(FlaskForm):
    username = TextField('Username')
    email = TextField('Email')
    password = PasswordField('Password')

class DiagramPropertiesForm(FlaskForm):
    node_choices = [(p, pretty_names[p]) for p in node_diagram_properties]
    node_properties = SelectMultipleField('Node properties', choices=node_choices)
    link_choices = [(p, pretty_names[p]) for p in link_diagram_properties]
    link_properties = SelectMultipleField('Link properties', choices=link_choices)
