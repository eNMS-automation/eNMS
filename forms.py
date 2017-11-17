from flask_wtf import FlaskForm
from helpers import napalm_getters
from wtforms import *
from wtforms.validators import DataRequired, EqualTo, Length, optional
from flask_wtf.file import FileAllowed
from netmiko.ssh_dispatcher import CLASS_MAPPER as netmiko_dispatcher

## Form for registering / logging in 

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
    
## Forms for managing devices
    
# devices can be added to the database either one by one via the AddDevice
# form, or all at once by importing an Excel or a CSV file.
class AddDevice(FlaskForm):
    ip_address = TextField('IP address', [optional()])
    password = PasswordField('Password', [optional()])
    os = TextField('Operating System', [optional()])
    hostname = TextField('Hostname', [optional()])
    secret = PasswordField('Secret password', [optional()])
    
class AddDevices(FlaskForm):
    device_file = FileField('', validators=[FileAllowed(['xls', 'xlsx', 'csv'], 'Excel or CSV file only')])
    
class DeleteDevice(FlaskForm):
    devices = SelectMultipleField('Devices', choices=())
    
## Forms for Netmiko
    
class NetmikoForm(FlaskForm):
    
    # exclude base driver from Netmiko available drivers
    exclude_base_driver = lambda driver: 'telnet' in driver or 'ssh' in driver
    netmiko_drivers = sorted(tuple(filter(exclude_base_driver, netmiko_dispatcher)))
    
    drivers = [(driver, driver) for driver in netmiko_drivers]
    driver = SelectField('', [optional()], choices=drivers)
    protocol_choices = (('Telnet',)*2, ('SSH',)*2)
    protocol = RadioField('', [optional()], choices=protocol_choices)
    global_delay_factor = FloatField('global_delay_factor', [optional()])
    raw_script = TextAreaField('', [optional(), Length(max=200)])
    file = FileField('', validators=[FileAllowed(['yaml'], 'YAML only')])
    devices = SelectMultipleField('Devices', choices=())
    
## Forms for NAPALM

class NapalmGettersForm(FlaskForm):
    # the list of devices is updated at rendering time by querying the database
    devices = SelectField('', [optional()], choices=())
    function_choices = [(function, function) for function in napalm_getters]
    functions = SelectMultipleField('Devices', choices=function_choices)
    output = TextAreaField('', [optional()])

class NapalmParametersForm(FlaskForm):
    protocol_choices = (('Telnet',)*2, ('SSH',)*2)
    protocol = RadioField('', [optional()], choices=protocol_choices)
    operation_choices = (('Commit merge',)*2, ('Commit replace',)*2)
    operation = RadioField('', [optional()], choices=operation_choices)
    raw_script = TextAreaField('', [optional(), Length(max=200)])
    file = FileField('', validators=[FileAllowed(['yaml'], 'YAML only')])
    devices = SelectMultipleField('Devices', choices=())
