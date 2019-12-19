from wtforms import (
    BooleanField,
    HiddenField,
    IntegerField,
    PasswordField,
    SelectField,
    StringField,
)
from wtforms.validators import InputRequired
from wtforms.widgets import TextArea

from eNMS import app
from eNMS.forms import BaseForm, configure_relationships
from eNMS.forms.fields import MultipleInstanceField
from eNMS.properties import private_properties
from eNMS.properties.objects import (
    device_icons,
    pool_link_properties,
    pool_device_properties,
)


def configure_device_form(cls):
    for property in app.custom_properties:
        field = PasswordField if property in private_properties else StringField
        setattr(cls, property, field())
    return cls


def configure_pool_form(cls):
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


class DeviceConnectionForm(BaseForm):
    template = "device_connection"
    form_type = HiddenField(default="device_connection")
    address_choices = [("ip_address", "IP address"), ("name", "Name")] + [
        (property, values["pretty_name"])
        for property, values in app.custom_properties.items()
        if values.get("is_address", False)
    ]
    address = SelectField(choices=address_choices)


class ObjectForm(BaseForm):
    form_type = HiddenField(default="object")
    name = StringField("Name", [InputRequired()])
    description = StringField("Description")
    subtype = StringField("Subtype")
    location = StringField("Location")
    vendor = StringField("Vendor")
    model = StringField("Model")


@configure_device_form
@configure_relationships
class DeviceForm(ObjectForm):
    template = "object"
    form_type = HiddenField(default="device")
    id = HiddenField()
    icon = SelectField("Icon", choices=tuple(device_icons.items()))
    ip_address = StringField("IP address")
    port = IntegerField("Port", default=22)
    operating_system = StringField("Operating System")
    os_version = StringField("OS Version")
    longitude = StringField("Longitude", default=0.0)
    latitude = StringField("Latitude", default=0.0)
    username = StringField("Username")
    password = PasswordField("Password")
    enable_password = PasswordField("'Enable' Password")
    napalm_driver = SelectField(
        "NAPALM Driver", choices=app.NAPALM_DRIVERS, default="ios"
    )
    netmiko_driver = SelectField(
        "Netmiko Driver", choices=app.NETMIKO_DRIVERS, default="cisco_ios"
    )


class DeviceDataForm(BaseForm):
    template = "device_data"
    form_type = HiddenField(default="device_data")
    data_type = SelectField(
        "Display",
        choices=(("configuration", "Configuration"), ("data", "Operational Data")),
    )


@configure_relationships
class LinkForm(ObjectForm):
    template = "object"
    form_type = HiddenField(default="link")
    id = HiddenField()
    color = StringField("Color")


@configure_pool_form
class PoolForm(BaseForm):
    template = "pool"
    form_type = HiddenField(default="pool")
    id = HiddenField()
    name = StringField("Name", [InputRequired()])
    description = StringField("Description")
    longitude = StringField("Longitude", default=0.0)
    latitude = StringField("Latitude", default=0.0)
    operator = SelectField(
        "Type of match",
        choices=(
            ("all", "Match if all properties match"),
            ("any", "Match if any property matches"),
        ),
    )
    never_update = BooleanField("Never update (for manually selected pools)")


class PoolObjectsForm(BaseForm):
    template = "pool_objects"
    form_type = HiddenField(default="pool_objects")
    devices = MultipleInstanceField("Devices")
    links = MultipleInstanceField("Links")
    string_devices = StringField(widget=TextArea(), render_kw={"rows": 5})
    string_links = StringField(widget=TextArea(), render_kw={"rows": 5})


class ExcelImportForm(BaseForm):
    template = "topology_import"
    form_type = HiddenField(default="excel_import")
    replace = BooleanField("Replace Existing Topology")


class ExportForm(BaseForm):
    action = "eNMS.exportTopology"
    form_type = HiddenField(default="excel_export")
    export_filename = StringField("Filename")
