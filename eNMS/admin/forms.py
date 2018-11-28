from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    FloatField,
    HiddenField,
    IntegerField,
    SelectField,
    StringField,
    PasswordField,
    SelectMultipleField
)

from eNMS.base.models import ObjectField
from eNMS.base.properties import import_properties, user_permissions


class LoginForm(FlaskForm):
    name = StringField()
    password = PasswordField()


class AddUser(FlaskForm):
    list_fields = HiddenField(default='permissions')
    id = HiddenField()
    name = StringField()
    password = PasswordField()
    email = StringField()
    permission_choices = [(p, p) for p in user_permissions]
    permissions = SelectMultipleField(choices=permission_choices)


class AdministrationForm(FlaskForm):
    boolean_fields = HiddenField(default='mattermost_verify_certificate')
    tacacs_ip_address = StringField('IP address')
    tacacs_password = PasswordField()
    tacacs_port = IntegerField(default=49)
    tacacs_timeout = IntegerField(default=10)
    syslog_ip_address = StringField('IP address', default='0.0.0.0')
    syslog_port = IntegerField(default=514)
    default_longitude = FloatField()
    default_latitude = FloatField()
    default_zoom_level = IntegerField()
    default_view = SelectField(choices=(
        ('2D', '2D View'),
        ('2DC', '2D Clusterized View'),
        ('3D', '3D View'),
    ))
    gotty_start_port = FloatField('Start port')
    gotty_end_port = FloatField('End port')
    mail_sender = StringField()
    mail_recipients = StringField()
    mattermost_url = StringField('Mattermost URL')
    mattermost_channel = StringField()
    mattermost_verify_certificate = BooleanField()
    slack_token = StringField()
    slack_channel = StringField()
    pool = ObjectField('Pool')
    categories = {
        'TACACS+ Client': (
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
            'default_zoom_level',
            'default_view'
        ),
        'SSH Terminal Parameters': (
            'gotty_start_port',
            'gotty_end_port'
        ),
        'Notification Parameters': (
            'mail_sender',
            'mail_recipients',
            'mattermost_url',
            'mattermost_channel',
            'mattermost_verify_certificate'
        ),
        'Horizontal Scaling': (
            'pool',
        )
    }


class MigrationsForm(FlaskForm):
    boolean_fields = HiddenField(default='empty_database_before_import')
    list_fields = HiddenField(default='import_export_types')
    empty_database_before_import = BooleanField()
    export_choices = [(p, p) for p in import_properties]
    import_export_types = SelectMultipleField(choices=export_choices)


class LogsForm(FlaskForm):
    clear_logs_date = StringField()


class AddInstance(FlaskForm):
    id = HiddenField()
    name = StringField()
    ip_address = StringField('IP address')
    weight = IntegerField()
