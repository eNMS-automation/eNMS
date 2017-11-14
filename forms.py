from flask_wtf import FlaskForm
from wtforms import TextField, PasswordField, SelectField, TextAreaField, RadioField, FileField
from wtforms.validators import DataRequired, EqualTo, Length, optional
from netmiko.ssh_dispatcher import CLASS_MAPPER as netmiko_dispatcher

class RegisterForm(FlaskForm):

    length_validator = [DataRequired(), Length(min=6, max=25)]
    match_constraint = EqualTo('password', message='Passwords must match')
    match_validator = [DataRequired(), match_constraint]

    name = TextField('Username', length_validator)
    email = TextField('Email', length_validator)
    password = PasswordField('Password', length_validator)
    confirm = PasswordField('Repeat Password', match_validator)

class LoginForm(FlaskForm):

    name = TextField('Username', [DataRequired()])
    password = PasswordField('Password', [DataRequired()])

class ForgotForm(FlaskForm):
    
    email = TextField('Email', validators=[DataRequired(), Length(min=6, max=40)])

class TestForm(FlaskForm):
    department = SelectField('', choices=())
    employee = SelectField('', choices=())
    
exclude_base_driver = lambda driver: 'telnet' in driver or 'ssh' in driver
netmiko_drivers = sorted(tuple(filter(exclude_base_driver, netmiko_dispatcher)))
    
class NetmikoParametersForm(FlaskForm):
    name = TextField('Username', [DataRequired()])
    password = PasswordField('Password', [DataRequired()])
    drivers = [(driver, driver) for driver in netmiko_drivers]
    department = SelectField('', choices=drivers)
    department2 = RadioField('', choices=(('Telnet', 'Telnet'), ('SSH', 'SSH')))
    employee = SelectField('', choices=())
    script = TextAreaField('', [optional(), Length(max=200)])
    file = FileField()