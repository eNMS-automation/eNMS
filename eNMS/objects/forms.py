from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    FloatField,
    HiddenField,
    IntegerField,
    PasswordField,
    SelectMultipleField,
    SelectField,
    TextField
)

from eNMS.base.properties import (
    custom_properties,
    link_public_properties,
    link_subtypes,
    device_public_properties,
    device_subtypes,
    import_properties
)


def configure_device_form(cls):
    for property in custom_properties:
        setattr(cls, property, TextField())
    return cls


def configure_pool_form(cls):
    cls.device_properties = device_public_properties
    cls.link_properties = link_public_properties
    for property in device_public_properties:
        setattr(cls, 'device_' + property, TextField(property))
        setattr(cls, 'device_' + property + '_regex', BooleanField('Regex'))
    for property in link_public_properties:
        setattr(cls, 'link_' + property, TextField(property))
        setattr(cls, 'link_' + property + '_regex', BooleanField('Regex'))
    return cls


class AddObjectForm(FlaskForm):
    id = HiddenField()
    name = TextField()
    description = TextField()
    location = TextField()
    vendor = TextField()
    model = TextField()


@configure_device_form
class AddDevice(AddObjectForm):
    device_types = [subtype for subtype in device_subtypes.items()]
    subtype = SelectField(choices=device_types)
    ip_address = TextField('IP address')
    port = IntegerField(default=22)
    operating_system = TextField()
    os_version = TextField()
    longitude = FloatField(default=0.)
    latitude = FloatField(default=0.)
    username = TextField()
    password = PasswordField()
    secret_password = PasswordField()


class AddLink(AddObjectForm):
    link_types = [subtype for subtype in link_subtypes.items()]
    subtype = SelectField(choices=link_types)
    source_name = SelectField()
    destination_name = SelectField()


@configure_pool_form
class AddPoolForm(FlaskForm):
    name = TextField()
    description = TextField()


class PoolObjectsForm(FlaskForm):
    devices = SelectMultipleField()
    links = SelectMultipleField()


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


class ImportExportForm(FlaskForm):
    name = TextField()
    export_choices = [(p, p.capitalize()) for p in import_properties]
    export = SelectMultipleField(choices=export_choices)
