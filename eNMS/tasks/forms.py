from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    IntegerField,
    SelectField,
    SelectMultipleField,
    TextField,
    TextAreaField
)


class SchedulingForm(FlaskForm):
    start_date = TextField('Start date')
    end_date = TextField('End date')
    name = TextField('Name')
    waiting_time = IntegerField('Waiting time', default=0)
    frequency = TextField('Frequency')
    run_immediately = BooleanField('Run immediately')
    do_not_run = BooleanField('Do not run', default=True)
    transfer_payload = BooleanField('Transfer payload', default=True)
    service_type_choices = (
        ('napalm_action', 'NAPALM action'),
        ('netmiko_config', 'Netmiko configuration'),
        ('napalm_config', 'NAPALM configuration'),
        ('napalm_getters', 'NAPALM getters'),
        ('file_transfer', 'File transfer'),
        ('netmiko_validation', 'Netmiko validation'),
        ('ansible_playbook', 'Ansible playbook'),
        ('custom_service', 'Custom services')
    )
    service_type = SelectField('Type of service', choices=service_type_choices)
    devices = SelectMultipleField('', choices=())
    pools = SelectMultipleField('', choices=())
    job = SelectField('', choices=())


class CompareForm(FlaskForm):
    first_version = SelectField('', choices=())
    second_version = SelectField('', choices=())
    first_device = SelectField('', choices=())
    second_device = SelectField('', choices=())
    unified_diff = TextAreaField('')
    ndiff = TextAreaField('')
