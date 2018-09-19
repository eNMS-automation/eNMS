from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed
from netmiko.ssh_dispatcher import CLASS_MAPPER
from wtforms import (
    BooleanField,
    FileField,
    FloatField,
    PasswordField,
    SelectField,
    SelectMultipleField,
    TextAreaField,
    TextField
)


class ServiceForm(FlaskForm):
    name = TextField('Name')
    description = TextField('Description')


class AnsibleServiceForm(ServiceForm):
    vendor = TextField('Vendor')
    operating_system = TextField('Operating system')
    playbook_path = TextField('Path to playbook')
    arguments = TextField('Optional arguments')
    inventory_from_selection = BooleanField()
    content_match = TextField('Content Match')
    content_match_regex = BooleanField()
    pass_device_properties = BooleanField()


class RestCallServiceForm(ServiceForm):
    choices = ('GET', 'POST', 'PUT', 'DELETE')
    call_type = SelectField('Type', choices=tuple(zip(choices, choices)))
    url = TextField('URL')
    payload = TextAreaField('Payload')
    username = TextField('Username')
    password = PasswordField('Password')
    content_match = TextField('Content Match')
    content_match_regex = BooleanField()
