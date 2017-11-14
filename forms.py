from flask_wtf import Form
from wtforms import TextField, PasswordField, SelectField, TextAreaField
from wtforms.validators import DataRequired, EqualTo, Length, optional

class RegisterForm(Form):

    length_validator = [DataRequired(), Length(min=6, max=25)]
    match_constraint = EqualTo('password', message='Passwords must match')
    match_validator = [DataRequired(), match_constraint]

    name = TextField('Username', length_validator)
    email = TextField('Email', length_validator)
    password = PasswordField('Password', length_validator)
    confirm = PasswordField('Repeat Password', match_validator)

class LoginForm(Form):

    name = TextField('Username', [DataRequired()])
    password = PasswordField('Password', [DataRequired()])

class ForgotForm(Form):
    
    email = TextField('Email', validators=[DataRequired(), Length(min=6, max=40)])

class TestForm(Form):
    department = SelectField('', choices=())
    employee = SelectField('', choices=())
    
class NetmikoParametersForm(Form):
    name = TextField('Username', [DataRequired()])
    password = PasswordField('Password', [DataRequired()])
    department = SelectField('', choices=())
    employee = SelectField('', choices=())
    script = TextAreaField('', [optional(), Length(max=200)])