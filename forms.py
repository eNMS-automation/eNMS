from flask_wtf import FlaskForm
from helpers import *
from wtforms import *
from wtforms.validators import DataRequired, EqualTo, Length, optional
from flask_wtf.file import FileAllowed
from netmiko.ssh_dispatcher import CLASS_MAPPER as netmiko_dispatcher

## Form for managing users

class AddUser(FlaskForm):
    
    username = TextField('Username')
    access_right_choices = (('Read-only',)*2, ('Read-write',)*2)
    access_rights = SelectField('Access rights', choices=access_right_choices)
    password = PasswordField('Password')
    secret_password = PasswordField('Secret password')
    
class DeleteUser(FlaskForm):
    users = SelectMultipleField('Users', choices=())
    
## Forms for managing devices
    
# devices can be added to the database either one by one via the AddDevice
# form, or all at once by importing an Excel or a CSV file.
class AddDevice(FlaskForm):
    hostname = TextField('Hostname', [optional()])
    ip_address = TextField('IP address', [optional()])
    vendor_choices = (('Cisco',)*2, ('Juniper',)*2)
    vendor = SelectField('Vendor', [optional()], choices=vendor_choices)
    operating_system = TextField('Operating System', [optional()])
    os_version = TextField('OS version', [optional()])
    longitude = FloatField('Longitude', [optional()])
    latitude = FloatField('Latitude', [optional()])
    
class AddDevices(FlaskForm):
    validators = [FileAllowed(['xls', 'xlsx', 'csv'], 'Excel or CSV file only')]
    file = FileField('', validators=validators)
    
class DeleteDevice(FlaskForm):
    devices = SelectMultipleField('Devices', choices=())
    
class AddLink(FlaskForm):
    source = SelectField('Source', choices=())
    destination = SelectField('Destination', choices=())
    
class SchedulingForm(FlaskForm):

    name = TextField('Name')
    
    scheduled_date = TextField('Datetime')
    
    frequency_choices = OrderedDict([
    ('Once', None),
    ('Every hour', 60*60),
    ('Once a day', 60*60*24),
    ('Once a week', 60*60*24*7),
    ('Once a month', 60*60*24*30),
    ])
    frequency_intervals = [(option, option) for option in frequency_choices]
    frequency = SelectField('', [optional()], choices=frequency_intervals)
    
## Forms for Netmiko
    
class NetmikoForm(SchedulingForm):
    
    user = SelectField('User', choices=())
    
    # exclude base driver from Netmiko available drivers
    exclude_base_driver = lambda driver: 'telnet' in driver or 'ssh' in driver
    netmiko_drivers = sorted(tuple(filter(exclude_base_driver, netmiko_dispatcher)))
    drivers = [(driver, driver) for driver in netmiko_drivers]
    driver = SelectField('', [optional()], choices=drivers)
    
    global_delay_factor = FloatField('global_delay_factor', [optional()], default=1.)
    
    raw_script = TextAreaField('', [optional(), Length(max=200)])
    
    file = FileField('', validators=[FileAllowed(['yaml'], 'YAML only')])
    
    devices = SelectMultipleField('Devices', choices=())
    
## Forms for NAPALM

class NapalmGettersForm(SchedulingForm):
    
    user = SelectField('User', choices=())

    devices = SelectMultipleField('', [optional()], choices=())
    
    getters_choices = [(getter, getter) for getter in getters_mapping]
    getters = SelectMultipleField('Devices', choices=getters_choices)
    
    output = TextAreaField('', [optional()])

class NapalmConfigurationForm(SchedulingForm):
    
    user = SelectField('User', choices=())
    
    action_choices = [(action, action) for action in napalm_actions]
    actions = SelectField('Actions', [optional()], choices=action_choices)
    
    file = FileField('', validators=[FileAllowed(['yaml'], 'YAML only')])
    
    devices = SelectMultipleField('Devices', choices=())
    
    raw_script = TextAreaField('', [optional(), Length(max=200)])
    