from flask_wtf import FlaskForm
from wtforms import *

## Login and registration

class LoginForm(FlaskForm):
    username = TextField('Username')
    password = PasswordField('Password')
    
class CreateAccountForm(FlaskForm):
    username = TextField('Username')
    email = TextField('Email')
    password = PasswordField('Password')
    