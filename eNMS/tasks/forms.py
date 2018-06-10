from flask_wtf import FlaskForm
from wtforms import SelectField, SelectMultipleField, TextField, TextAreaField


class SchedulingForm(FlaskForm):
    start_date = TextField('Start date')
    end_date = TextField('End date')
    name = TextField('Name')
    frequency = TextField('Frequency')
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
    nodes = SelectMultipleField('', choices=())
    pools = SelectMultipleField('', choices=())
    scripts = SelectMultipleField('', choices=())


class CompareForm(FlaskForm):
    first_version = SelectField('', choices=())
    second_version = SelectField('', choices=())
    first_node = SelectField('', choices=())
    second_node = SelectField('', choices=())
    first_script = SelectField('', choices=())
    second_script = SelectField('', choices=())
    unified_diff = TextAreaField('')
    ndiff = TextAreaField('')
