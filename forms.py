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
    driver = SelectField('', [optional()], choices=drivers)
    protocol = RadioField('', [optional()], choices=(('Telnet', 'Telnet'), ('SSH', 'SSH')))
    global_delay_factor = FloatField('global_delay_factor', [optional()])
    employee = SelectField('', [optional()], choices=())
    raw_script = TextAreaField('', [optional(), Length(max=200)])
    file = FileField('', validators=[FileAllowed(['yaml'], 'YAML only')])
    
class NetmikoDevicesForm(FlaskForm):
    assigned = SelectMultipleField('Assigned', choices=())
    script = TextAreaField('', [optional(), Length(max=200)])

# devices can be added to the database either one by one via the AddDevice
# form, or all at once by importing an Excel or a CSV file.
class AddDevice(FlaskForm):
    ip_address = TextField('IP address', [DataRequired()])
    password = PasswordField('Password', [DataRequired()])
    os = TextField('Operating System', [DataRequired()])
    hostname = TextField('Hostname', [])
    secret = PasswordField('Secret password', [])
    
class AddDevices(FlaskForm):
    device_file = FileField('', validators=[FileAllowed(['xls', 'xlsx', 'csv'], 'Excel or CSV file only')])
    
class DeleteDevice(FlaskForm):
    devices = SelectMultipleField('Devices', choices=())
