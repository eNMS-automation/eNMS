from flask_wtf import FlaskForm
from wtforms import *
from objects.properties import *

## Login and registration

class LoginForm(FlaskForm):
    username = TextField('Username')
    password = PasswordField('Password')
    
class CreateAccountForm(FlaskForm):
    username = TextField('Username')
    email = TextField('Email')
    password = PasswordField('Password')

class NodePropertiesForm(FlaskForm):
    property_choices = [(p, pretty_names[p]) for p in node_public_properties]
    properties = SelectMultipleField('Node properties', choices=property_choices)

class LinkPropertiesForm(FlaskForm):
    property_choices = [(p, pretty_names[p]) for p in link_public_properties]
    properties = SelectMultipleField('Link properties', choices=property_choices)