from collections import OrderedDict
from flask_wtf import FlaskForm
from helpers2 import *
from wtforms import *
from wtforms.validators import DataRequired, EqualTo, Length, optional
from flask_wtf.file import FileAllowed

## Login and registration

class LoginForm(FlaskForm):
    username = TextField('Username')
    password = PasswordField('Password')
    
class CreateAccountForm(FlaskForm):
    username = TextField('Username')
    email = TextField('Email')
    password = PasswordField('Password')
    
