from flask_wtf import FlaskForm
from wtforms import SelectField, SelectMultipleField, TextField


class AddScriptForm(FlaskForm):
    script_type_choices = (
        ('napalm_action', 'NAPALM action'),
        ('netmiko_config', 'Netmiko configuration'),
        ('napalm_config', 'NAPALM configuration'),
        ('napalm_getters', 'NAPALM getters'),
        ('file_transfer', 'File transfer'),
        ('netmiko_validation', 'Netmiko validation'),
        ('ansible_playbook', 'Ansible playbook'),
        ('custom_script', 'Custom scripts')
    )
    script_type = SelectField('Type of script', choices=script_type_choices)
    scripts = SelectMultipleField('', choices=())


class WorkflowCreationForm(FlaskForm):
    name = TextField('Name')
    description = TextField('Description')
    type = TextField('Type')
