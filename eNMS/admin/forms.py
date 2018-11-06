from wtforms import (
    FloatField,
    HiddenField,
    IntegerField,
    TextField,
    PasswordField,
    SelectField,
    SelectMultipleField
)

from eNMS.base.models import BaseForm
from eNMS.base.properties import import_properties, user_permissions


class LoginForm(BaseForm):
    name = TextField()
    password = PasswordField()


class CreateAccountForm(BaseForm):
    name = TextField()
    email = TextField()
    password = PasswordField()


class AddUser(BaseForm):
    id = HiddenField()
    name = TextField()
    password = PasswordField()
    email = TextField()
    permission_choices = [(p, p) for p in user_permissions]
    permissions = SelectMultipleField(choices=permission_choices)


class AdministrationForm(BaseForm):
    tacacs_ip_address = TextField('IP address')
    tacacs_password = PasswordField()
    tacacs_port = IntegerField(default=49)
    tacacs_timeout = IntegerField(default=10)
    syslog_ip_address = TextField('IP address', default='0.0.0.0')
    syslog_port = IntegerField(default=514)
    default_longitude = FloatField()
    default_latitude = FloatField()
    default_zoom_level = IntegerField()
    gotty_start_port = FloatField('Start port')
    gotty_end_port = FloatField('End port')
    mail_sender = TextField()
    mail_recipients = TextField()
    mattermost_url = TextField('Mattermost URL')
    mattermost_channel = TextField()
    pool = SelectField(choices=())
    categories = {
        'TACACS+ Server': (
            'tacacs_ip_address',
            'tacacs_password',
            'tacacs_port',
            'tacacs_timeout'
        ),
        'Syslog Server': (
            'syslog_ip_address',
            'syslog_port',
        ),
        'Geographical Parameters': (
            'default_longitude',
            'default_latitude',
            'default_zoom_level'
        ),
        'SSH Terminal Parameters': (
            'gotty_start_port',
            'gotty_end_port'
        ),
        'Notification Parameters': (
            'mail_sender',
            'mail_recipients',
            'mattermost_url',
            'mattermost_channel'
        ),
        'Horizontal Scaling': (
            'pool',
        )
    }


class ImportExportForm(BaseForm):
    name = TextField()
    export_choices = [(p, p.capitalize()) for p in import_properties]
    export = SelectMultipleField(choices=export_choices)
