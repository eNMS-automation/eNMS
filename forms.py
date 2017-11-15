from flask_wtf import FlaskForm
from wtforms import *
from wtforms.validators import DataRequired, EqualTo, Length, optional
from flask_wtf.file import FileAllowed
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
    
class NetmikoParametersForm(FlaskForm):
    
    # exclude base driver from Netmiko available drivers
    exclude_base_driver = lambda driver: 'telnet' in driver or 'ssh' in driver
    netmiko_drivers = sorted(tuple(filter(exclude_base_driver, netmiko_dispatcher)))
    
    drivers = [(driver, driver) for driver in netmiko_drivers]
    department = SelectField('', [optional()], choices=drivers)
    department2 = RadioField('', [optional()], choices=(('Telnet', 'Telnet'), ('SSH', 'SSH')))
    employee = SelectField('', [optional()], choices=())
    script = TextAreaField('', [optional(), Length(max=200)])
    file = FileField('', validators=[FileAllowed(['yaml'], 'YAML only')])
    
class NetmikoDevicesForm(FlaskForm):
    department2 = RadioField('', [optional()], choices=(('Telnet', 'Telnet'), ('SSH', 'SSH')))
    employee = SelectField('', [optional()], choices=())
    assigned = SelectMultipleField('Assigned', choices=())
    script = TextAreaField('', [optional(), Length(max=200)])
    file = FileField('', validators=[FileAllowed(['yaml'], 'YAML only')])

class AddOneDevice(FlaskForm):
    hostname = TextField('Hostname', [])
    ip_address = TextField('IP address', [DataRequired()])
    password = PasswordField('Password', [DataRequired()])
    secret = PasswordField('Secret password', [])
