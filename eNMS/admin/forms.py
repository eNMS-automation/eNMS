from flask_wtf import FlaskForm
from wtforms import (
    FloatField,
    HiddenField,
    IntegerField,
    TextField,
    PasswordField,
    SelectField,
    SelectMultipleField
)

from eNMS.base.properties import user_permissions


class LoginForm(FlaskForm):
    name = TextField()
    password = PasswordField()


class CreateAccountForm(FlaskForm):
    name = TextField()
    email = TextField()
    password = PasswordField()


class AddUser(FlaskForm):
    id = HiddenField()
    name = TextField()
    password = PasswordField()
    email = TextField()
    permission_choices = [(p, p) for p in user_permissions]
    permissions = SelectMultipleField(choices=permission_choices)


class TacacsServerForm(FlaskForm):
    ip_address = TextField('IP address')
    password = PasswordField()
    port = IntegerField(default=49)
    timeout = IntegerField(default=10)


class SyslogServerForm(FlaskForm):
    ip_address = TextField('IP address', default='0.0.0.0')
    port = IntegerField(default=514)


class GeographicalParametersForm(FlaskForm):
    default_longitude = FloatField()
    default_latitude = FloatField()
    default_zoom_level = IntegerField()


class GottyParametersForm(FlaskForm):
    gotty_start_port = FloatField('Start port')
    gotty_end_port = FloatField('End port')


class NotificationParametersForm(FlaskForm):
    mail_sender = TextField()
    mail_recipients = TextField()
    mattermost_url = TextField('Mattermost URL')
    mattermost_channel = TextField()


class DatabaseFilteringForm(FlaskForm):
    pool = SelectField(choices=())
