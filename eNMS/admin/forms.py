from flask_wtf import FlaskForm
from wtforms import (
    FloatField,
    IntegerField,
    TextField,
    PasswordField,
    SelectField,
    SelectMultipleField
)

from eNMS.base.properties import device_subtypes, user_permissions


class LoginForm(FlaskForm):
    name = TextField()
    password = PasswordField()


class CreateAccountForm(FlaskForm):
    name = TextField()
    email = TextField()
    password = PasswordField()


class AddUser(FlaskForm):
    name = TextField()
    password = PasswordField()
    email = TextField()
    permission_choices = [(p, p) for p in user_permissions]
    permissions = SelectMultipleField(choices=permission_choices)


class TacacsServerForm(FlaskForm):
    ip_address = TextField()
    password = PasswordField()
    port = IntegerField(default=49)
    timeout = IntegerField(default=10)


class SyslogServerForm(FlaskForm):
    ip_address = TextField(default='0.0.0.0')
    port = IntegerField(default=514)


class GeographicalParametersForm(FlaskForm):
    default_longitude = FloatField()
    default_latitude = FloatField()
    default_zoom_level = IntegerField()


class GottyParametersForm(FlaskForm):
    gotty_start_port = FloatField('Start port')
    gotty_end_port = FloatField('End port')


class OpenNmsForm(FlaskForm):
    rest_query = TextField(
        'ReST API',
        default='https://demo.opennms.org/opennms/rest'
    )
    node_query = TextField(
        'Devices',
        default='https://demo.opennms.org/opennms/rest/nodes'
    )
    node_type = [subtype for subtype in device_subtypes.items()]
    type = SelectField('Type', choices=node_type)
    login = TextField('Login')
    password = PasswordField('Password')


class NetboxForm(FlaskForm):
    netbox_address = TextField('Address', default='http://0.0.0.0:8000')
    netbox_token = TextField('Token')
    node_type = [subtype for subtype in device_subtypes.items()]
    netbox_type = SelectField('Type', choices=node_type)
