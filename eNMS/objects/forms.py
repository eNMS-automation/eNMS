from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    FloatField,
    HiddenField,
    PasswordField,
    SelectMultipleField,
    SelectField,
    TextField
)

from eNMS.base.properties import (
    link_public_properties,
    link_subtypes,
    device_public_properties,
    device_subtypes
)


class AddObjectForm(FlaskForm):
    id = HiddenField()
    name = TextField()
    description = TextField()
    location = TextField()
    vendor = TextField()
    model = TextField()

# devices can be added to the database either one by one via the AddDevice
# form, or all at once by importing an Excel or a CSV file.


class AddDevice(AddObjectForm):
    device_types = [subtype for subtype in device_subtypes.items()]
    subtype = SelectField(choices=device_types)
    ip_address = TextField('IP address')
    port = TextField()
    operating_system = TextField()
    os_version = TextField()
    longitude = FloatField(default=0.)
    latitude = FloatField(default=0.)
    username = TextField()
    password = PasswordField()
    secret_password = PasswordField()
    property1 = FloatField()
    property2 = TextField()


class AddLink(AddObjectForm):
    link_types = [subtype for subtype in link_subtypes.items()]
    subtype = SelectField(choices=link_types)
    source = SelectField()
    destination = SelectField()


def configure_form(cls):
    cls.device_properties = device_public_properties
    cls.link_properties = link_public_properties
    for property in device_public_properties:
        setattr(cls, 'device_' + property, TextField(property))
        setattr(cls, 'device_' + property + '_regex', BooleanField('Regex'))
    for property in link_public_properties:
        setattr(cls, 'link_' + property, TextField(property))
        setattr(cls, 'link_' + property + '_regex', BooleanField('Regex'))
    return cls


@configure_form
class AddPoolForm(FlaskForm):
    name = TextField()
    description = TextField()


class PoolObjectsForm(FlaskForm):
    devices = SelectMultipleField()
    links = SelectMultipleField()
