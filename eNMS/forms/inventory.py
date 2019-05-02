from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    FloatField,
    HiddenField,
    IntegerField,
    PasswordField,
    SelectField,
    StringField,
)

from eNMS.controller import controller
from eNMS.forms import metaform
from eNMS.forms.fields import MultipleObjectField, ObjectField
from eNMS.properties import (
    custom_properties,
    pool_link_properties,
    link_subtypes,
    pool_device_properties,
    device_subtypes,
)


def configure_device_form(cls: FlaskForm) -> FlaskForm:
    for property in custom_properties:
        setattr(cls, property, StringField())
    return cls


def configure_pool_form(cls: FlaskForm) -> FlaskForm:
    cls.device_properties = pool_device_properties
    cls.link_properties = pool_link_properties
    for cls_name, properties in (
        ("device", pool_device_properties),
        ("link", pool_link_properties),
    ):
        for property in properties:
            match_field = f"{cls_name}_{property}_match"
            setattr(cls, f"{cls_name}_{property}", StringField(property))
            setattr(
                cls,
                match_field,
                SelectField(
                    choices=(
                        ("inclusion", "Inclusion"),
                        ("equality", "Equality"),
                        ("regex", "Regular Expression"),
                    )
                ),
            )
    return cls


class ConnectionForm(FlaskForm, metaclass=metaform):
    template = "connection"
    form_type = HiddenField(default="connection")
    address_choices = [("ip_address", "IP address"), ("name", "Name")] + [
        (property, values["pretty_name"])
        for property, values in custom_properties.items()
        if values.get("is_address", False)
    ]
    address = SelectField(choices=address_choices)


class ObjectFilteringForm(FlaskForm, metaclass=metaform):
    action = "filter"
    form_type = HiddenField(default="device_filtering,link_filtering")
    pools = MultipleObjectField("Pool")


class ObjectForm(FlaskForm):
    name = StringField()
    description = StringField()
    location = StringField()
    vendor = StringField()
    model = StringField()


@configure_device_form
class DeviceFilteringForm(ObjectFilteringForm, ObjectForm, metaclass=metaform):
    form_type = HiddenField(default="device_filtering")
    current_configuration = StringField()
    subtype = StringField()
    ip_address = StringField()
    port = StringField()
    operating_system = StringField()
    os_version = StringField()
    longitude = StringField()
    latitude = StringField()
    napalm_driver = StringField()
    netmiko_driver = StringField()


@configure_device_form
class DeviceForm(ObjectForm, metaclass=metaform):
    template = "object"
    form_type = HiddenField(default="device")
    id = HiddenField()
    device_types = [subtype for subtype in device_subtypes.items()]
    subtype = SelectField(choices=device_types)
    ip_address = StringField("IP address")
    port = IntegerField(default=22)
    operating_system = StringField()
    os_version = StringField()
    longitude = FloatField(default=0.0)
    latitude = FloatField(default=0.0)
    username = StringField()
    password = PasswordField()
    enable_password = PasswordField()
    napalm_driver = SelectField(choices=controller.NAPALM_DRIVERS)
    netmiko_driver = SelectField(choices=controller.NETMIKO_DRIVERS)


class LinkForm(ObjectForm, metaclass=metaform):
    template = "object"
    form_type = HiddenField(default="link")
    id = HiddenField()
    link_types = [subtype for subtype in link_subtypes.items()]
    subtype = SelectField(choices=link_types)
    source = ObjectField("Device")
    destination = ObjectField("Device")


class LinkFilteringForm(ObjectForm, ObjectFilteringForm, metaclass=metaform):
    form_type = HiddenField(default="link_filtering")
    subtype = StringField()
    source_name = StringField()
    destination_name = StringField()


@configure_pool_form
class PoolForm(FlaskForm, metaclass=metaform):
    template = "pool"
    form_type = HiddenField(default="pool")
    id = HiddenField()
    name = StringField()
    description = StringField()
    longitude = FloatField(default=0.0)
    latitude = FloatField(default=0.0)
    operator = SelectField(
        choices=(
            ("all", "Match if all properties match"),
            ("any", "Match if any property matches"),
        )
    )
    never_update = BooleanField("Never update (for manually selected pools)")


class PoolFilteringForm(FlaskForm, metaclass=metaform):
    action = filter
    form_type = HiddenField(default="pool_filtering")
    name = StringField()
    description = StringField()
    longitude = StringField()
    latitude = StringField()
    operator = StringField()


class PoolObjectsForm(FlaskForm, metaclass=metaform):
    form_type = HiddenField(default="pool_objects")
    devices = MultipleObjectField("Device")
    links = MultipleObjectField("Link")


class ExcelImportForm(FlaskForm, metaclass=metaform):
    template = "topology_import"
    form_type = HiddenField(default="excel")
    replace = BooleanField()


class OpenNmsForm(FlaskForm, metaclass=metaform):
    action = "queryOpenNMS"
    form_type = HiddenField(default="opennms")
    opennms_rest_api = StringField()
    opennms_devices = StringField()
    node_type = [subtype for subtype in device_subtypes.items()]
    subtype = SelectField(choices=node_type)
    opennms_login = StringField()
    password = PasswordField()


class NetboxForm(FlaskForm, metaclass=metaform):
    action = "queryNetbox"
    form_type = HiddenField(default="netbox")
    netbox_address = StringField(default="http://0.0.0.0:8000")
    netbox_token = PasswordField()
    node_type = [subtype for subtype in device_subtypes.items()]
    netbox_type = SelectField(choices=node_type)


class LibreNmsForm(FlaskForm, metaclass=metaform):
    action = "queryLibreNMS"
    form_type = HiddenField(default="librenms")
    librenms_address = StringField(default="http://librenms.example.com")
    node_type = [subtype for subtype in device_subtypes.items()]
    librenms_type = SelectField(choices=node_type)
    librenms_token = PasswordField()


class ExportForm(FlaskForm, metaclass=metaform):
    action = "exportTopology"
    form_type = HiddenField(default="excel_export")
    export_filename = StringField()


class GoogleEarthForm(FlaskForm, metaclass=metaform):
    form_type = HiddenField(default="google_earth_export")
    name = StringField()
    label_size = IntegerField(default=1)
    line_width = IntegerField(default=2)


class CompareConfigurationsForm(FlaskForm, metaclass=metaform):
    template = "configuration"
    form_type = HiddenField(default="configuration")
    display = SelectField(choices=())
    compare_with = SelectField(choices=())
