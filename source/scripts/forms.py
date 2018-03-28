from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed
from wtforms import TextField, SelectField, TextAreaField, FileField

ansible_options = {
    'listtags': ('List of tags', False),
    'listtasks': ('List of tasks', False),
    'listhosts': ('List of hosts', False),
    'syntax': ('Syntax', False),
    'connection': ('Connection', 'ssh'),
    'module_path': ('Module path', None),
    'forks': ('Number of forks', 100),
    'remote_user': ('Remote user', None),
    'private_key_file': ('Private key file', None),
    'ssh_common_args': ('SSH common arguments', None),
    'ssh_extra_args': ('SSH extra arguments', None),
    'sftp_extra_args': ('SFTP extra arguments', None),
    'scp_extra_args': ('SCP extra arguments', None),
    'become': ('Become', False),
    'become_method': ('Become method', None),
    'become_user': ('Become user', None),
    'verbosity': ('Verbosity', None),
    'check': ('Check', False),
    'diff': ('Diff', False)
}


class ConfigScriptForm(FlaskForm):
    name = TextField('Name')
    type_choices = (
        ('simple', 'Simple'),
        ('j2_template', 'Jinja2 template'),
        ('per_device_j2', 'Per-device Jinja2 template')
    )
    type = SelectField('', choices=type_choices)
    text = TextAreaField('')
    file = FileField('', validators=[FileAllowed(['yaml'], 'YAML only')])


class FileTransferScriptForm(FlaskForm):
    name = TextField('Name')
    driver_choices = (
        ('cisco_ios', 'Cisco IOS'),
        ('cisco_xe', 'Cisco IOS-XE'),
        ('cisco_xr', 'Cisco IOS-XR'),
        ('cisco_nxos', 'Cisco NX-OS'),
        ('juniper_junos', 'Juniper'),
        ('arista_eos', 'Arista')
    )
    driver = SelectField('', choices=driver_choices)
    source_file = TextField('Source file')
    destination_file = TextField('Destination file')
    file_system = TextField('File system')
    direction_choices = (('put', 'Upload'), ('get', 'Download'))
    direction = SelectField('', choices=direction_choices)


def configure_form(cls):
    for option, (pretty_name, default_value) in ansible_options.items():
        setattr(cls, option, TextField(pretty_name, default=default_value))
    return cls


@configure_form
class AnsibleScriptForm(FlaskForm):
    name = TextField('Name')


class WorkflowCreationForm(FlaskForm):
    name = TextField('Name')
    netmiko_scripts = SelectField('', choices=())
    napalm_scripts = SelectField('', choices=())
    ansible_scripts = SelectField('', choices=())