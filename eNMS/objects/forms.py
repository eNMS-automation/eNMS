from wtforms import (
    BooleanField,
    FloatField,
    HiddenField,
    IntegerField,
    PasswordField,
    SelectMultipleField,
    SelectField,
    StringField
)

from eNMS.base.models import BaseForm
from eNMS.base.properties import (
    custom_properties,
    link_public_properties,
    link_subtypes,
    device_public_properties,
    device_subtypes
)


def configure_device_form(cls):
    for property in custom_properties:
        setattr(cls, property, StringField())
    return cls


def configure_pool_form(cls):
    cls.device_properties = device_public_properties
    cls.link_properties = link_public_properties
    for property in device_public_properties:
        setattr(cls, 'device_' + property, StringField(property))
        setattr(cls, 'device_' + property + '_regex', BooleanField('Regex'))
    for property in link_public_properties:
        setattr(cls, 'link_' + property, StringField(property))
        setattr(cls, 'link_' + property + '_regex', BooleanField('Regex'))
    return cls


class AddObjectForm(BaseForm):
    id = HiddenField()
    name = StringField()
    description = StringField()
    location = StringField()
    vendor = StringField()
    model = StringField()


@configure_device_form
class AddDevice(AddObjectForm):
    device_types = [subtype for subtype in device_subtypes.items()]
    subtype = SelectField(choices=device_types)
    ip_address = StringField('IP address')
    port = IntegerField(default=22)
    operating_system = StringField()
    os_version = StringField()
    longitude = FloatField(default=0.)
    latitude = FloatField(default=0.)
    username = StringField()
    password = PasswordField()
    secret_password = PasswordField()


class AddLink(AddObjectForm):
    link_types = [subtype for subtype in link_subtypes.items()]
    subtype = SelectField(choices=link_types)
    source = SelectField()
    destination = SelectField()


@configure_pool_form
class AddPoolForm(BaseForm):
    name = StringField()
    description = StringField()


class PoolObjectsForm(BaseForm):
    devices = SelectMultipleField()
    links = SelectMultipleField()


class OpenNmsForm(BaseForm):
    opennms_rest_api = StringField()
    opennms_devices = StringField()
    node_type = [subtype for subtype in device_subtypes.items()]
    subtype = SelectField(choices=node_type)
    opennms_login = StringField()
    password = PasswordField()


class NetboxForm(BaseForm):
    netbox_address = StringField(default='http://0.0.0.0:8000')
    netbox_token = StringField()
    node_type = [subtype for subtype in device_subtypes.items()]
    netbox_type = SelectField(choices=node_type)
