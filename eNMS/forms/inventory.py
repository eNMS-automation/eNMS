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
from eNMS.forms import BaseForm
from eNMS.forms.fields import MultipleInstanceField, InstanceField
from eNMS.properties.objects import (
    device_subtypes,
    link_subtypes,
    pool_link_properties,
    pool_device_properties,
)


def configure_device_form(cls: BaseForm) -> BaseForm:
    for property in controller.custom_properties:
        setattr(cls, property, StringField())
    return cls


def configure_pool_form(cls: BaseForm) -> BaseForm:
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


class ConnectionForm(BaseForm):
    template = "connection"
    form_type = HiddenField(default="connection")
    address_choices = [("ip_address", "IP address"), ("name", "Name")] + [
        (property, values["pretty_name"])
        for property, values in controller.custom_properties.items()
        if values.get("is_address", False)
    ]
    address = SelectField(choices=address_choices)


class ObjectFilteringForm(BaseForm):
    action = "filter"
    form_type = HiddenField(default="object_filtering")
    pools = MultipleInstanceField("Pools", instance_type="Pool")


class ObjectForm(BaseForm):
    form_type = HiddenField(default="object")
    name = StringField("Name")
    description = StringField("Description")
    location = StringField("Location")
    vendor = StringField("Vendor")
    model = StringField("Model")


@configure_device_form
class DeviceFilteringForm(ObjectFilteringForm, ObjectForm):
    form_type = HiddenField(default="device_filtering")
    current_configuration = StringField("Current Configuration")
    subtype = StringField("Subtype")
    ip_address = StringField("IP Address")
    port = StringField("Port")
    operating_system = StringField("Operating System")
    os_version = StringField("OS Version")
    longitude = StringField("Longitude")
    latitude = StringField("Latitude")
    napalm_driver = StringField("NAPALM Driver")
    netmiko_driver = StringField("Netmiko Driver")


@configure_device_form
class DeviceForm(ObjectForm):
    template = "object"
    form_type = HiddenField(default="device")
    id = HiddenField()
    subtype = SelectField("Subtype", choices=tuple(device_subtypes.items()))
    ip_address = StringField("IP address")
    port = IntegerField("Port", default=22)
    operating_system = StringField("Operating System")
    os_version = StringField("OS Version")
    longitude = FloatField("Longitude", default=0.0)
    latitude = FloatField("Latitude", default=0.0)
    username = StringField("Username")
    password = PasswordField("Password")
    enable_password = PasswordField("'Enable' Password")
    napalm_driver = SelectField(
        "NAPALM Driver", choices=controller.NAPALM_DRIVERS, default="ios"
    )
    netmiko_driver = SelectField(
        "Netmiko Driver", choices=controller.NETMIKO_DRIVERS, default="cisco_ios"
    )


class LinkForm(ObjectForm):
    template = "object"
    form_type = HiddenField(default="link")
    id = HiddenField()
    subtype = SelectField("Subtype", choices=tuple(link_subtypes.items()))
    source = InstanceField("Source", instance_type="Device")
    destination = InstanceField("Destination", instance_type="Device")


class LinkFilteringForm(ObjectForm, ObjectFilteringForm):
    form_type = HiddenField(default="link_filtering")
    subtype = StringField("Subtype")
    source_name = StringField("Source")
    destination_name = StringField("Destination")


@configure_pool_form
class PoolForm(BaseForm):
    template = "pool"
    form_type = HiddenField(default="pool")
    id = HiddenField()
    name = StringField("Name")
    description = StringField("Description")
    longitude = FloatField("Longitude", default=0.0)
    latitude = FloatField("Latitude", default=0.0)
    operator = SelectField(
        "Match Condition",
        choices=(
            ("all", "Match if all properties match"),
            ("any", "Match if any property matches"),
        ),
    )
    never_update = BooleanField("Never update (for manually selected pools)")


class PoolFilteringForm(BaseForm):
    action = filter
    form_type = HiddenField(default="pool_filtering")
    name = StringField("Name")
    description = StringField("Description")
    longitude = FloatField("Longitude")
    latitude = FloatField("Latitude")
    operator = StringField("Match Condition")


class PoolObjectsForm(BaseForm):
    template = "pool_objects"
    form_type = HiddenField(default="pool_objects")
    devices = MultipleInstanceField("Devices", instance_type="Device")
    links = MultipleInstanceField("Links", instance_type="Link")


class ExcelImportForm(BaseForm):
    template = "topology_import"
    form_type = HiddenField(default="excel_import")
    replace = BooleanField("Replace Existing Topology")


class OpenNmsForm(BaseForm):
    action = "queryOpenNMS"
    form_type = HiddenField(default="opennms")
    opennms_rest_api = StringField("REST API URL")
    opennms_devices = StringField("Devices")
    subtype = SelectField("Subtype", choices=tuple(device_subtypes.items()))
    opennms_login = StringField("Login")
    password = PasswordField("Password")


class NetboxForm(BaseForm):
    action = "queryNetbox"
    form_type = HiddenField(default="netbox")
    netbox_address = StringField("URL", default="http://0.0.0.0:8000")
    netbox_token = PasswordField("Token")
    netbox_type = SelectField(choices=tuple(device_subtypes.items()))


class LibreNmsForm(BaseForm):
    action = "queryLibreNMS"
    form_type = HiddenField(default="librenms")
    librenms_address = StringField("URL", default="http://librenms.example.com")
    librenms_type = SelectField("Subtype", choices=tuple(device_subtypes.items()))
    librenms_token = PasswordField("Token")


class ExportForm(BaseForm):
    action = "exportTopology"
    form_type = HiddenField(default="excel_export")
    export_filename = StringField("Filename")


class GoogleEarthForm(BaseForm):
    action = "exportToGoogleEarth"
    form_type = HiddenField(default="google_earth_export")
    name = StringField("Name")
    label_size = IntegerField("Label Size", default=1)
    line_width = IntegerField("Link Width", default=2)


class CompareConfigurationsForm(BaseForm):
    template = "configuration"
    form_type = HiddenField(default="configuration")
    display = SelectField("Version to display", choices=())
    compare_with = SelectField("Compare Against", choices=())
