from flask_wtf import FlaskForm
from wtforms import *

class AddUser(FlaskForm):
    
    username = TextField('Username')
    email = TextField('Email')
    access_right_choices = (('Read-only',)*2, ('Read-write',)*2)
    access_rights = SelectField('Access rights', choices=access_right_choices)
    password = PasswordField('Password')
    secret_password = PasswordField('Secret password')
    
class DeleteUser(FlaskForm):
    users = SelectMultipleField('Users', choices=())