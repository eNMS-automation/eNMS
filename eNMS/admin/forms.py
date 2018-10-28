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

from eNMS.base.classes import diagram_classes
from eNMS.base.properties import device_subtypes, user_permissions


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


class OpenNmsForm(FlaskForm):
    opennms_rest_api = TextField()
    opennms_devices = TextField()
    node_type = [subtype for subtype in device_subtypes.items()]
    subtype = SelectField(choices=node_type)
    opennms_login = TextField()
    password = PasswordField()


class NetboxForm(FlaskForm):
    netbox_address = TextField(default='http://0.0.0.0:8000')
    netbox_token = TextField()
    node_type = [subtype for subtype in device_subtypes.items()]
    netbox_type = SelectField(choices=node_type)


class ExportForm(FlaskForm):
    export_choices = [(k, c.__tablename__) for k, c in diagram_classes.items()]
    export = SelectMultipleField(choices=export_choices)
