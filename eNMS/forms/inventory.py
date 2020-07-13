from wtforms.validators import InputRequired
from wtforms.widgets import TextArea

from eNMS import app
from eNMS.forms import BaseForm, choices
from eNMS.forms.fields import (
    BooleanField,
    HiddenField,
    InstanceField,
    IntegerField,
    MultipleInstanceField,
    PasswordField,
    SelectField,
    StringField,
)


def configure_pool_form(cls):
    cls.device_properties = app.properties["filtering"]["device"]
    cls.link_properties = app.properties["filtering"]["link"]
    for cls_name, properties in (
        ("device", app.properties["filtering"]["device"]),
        ("link", app.properties["filtering"]["link"]),
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
        for property, values in app.properties["custom"]["device"].items()
        if values.get("is_address", False)
    ]
    address = SelectField(choices=address_choices)
    username = StringField("Username")
    password = PasswordField("Password")


class ObjectForm(BaseForm):
    form_type = HiddenField(default="object")
    name = StringField("Name", [InputRequired()])
    public = BooleanField("Public", default=False)
    description = StringField("Description")
    subtype = StringField("Subtype")
    location = StringField("Location")
    vendor = StringField("Vendor")
    model = StringField("Model")


class DeviceForm(ObjectForm):
    template = "object"
    form_type = HiddenField(default="device")
    id = HiddenField()
    icon = SelectField(
        "Icon",
        choices=(
            ("antenna", "Antenna"),
            ("firewall", "Firewall"),
            ("host", "Host"),
            ("optical_switch", "Optical switch"),
            ("regenerator", "Regenerator"),
            ("router", "Router"),
            ("server", "Server"),
            ("switch", "Switch"),
        ),
    )
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
    scrapli_driver = SelectField(
        "Scrapli Driver", choices=choices(app.SCRAPLI_DRIVERS), default="cisco_iosxe"
    )


class DeviceDataForm(BaseForm):
    template = "device_data"
    form_type = HiddenField(default="device_data")
    data_type = SelectField("Display", choices=app.configuration_properties)


class LinkForm(ObjectForm):
    template = "object"
    form_type = HiddenField(default="link")
    id = HiddenField()
    source = InstanceField("Source", [InputRequired()], model="device")
    destination = InstanceField("Destination", [InputRequired()], model="device")
    color = StringField("Color")


@configure_pool_form
class PoolForm(BaseForm):
    template = "pool"
    form_type = HiddenField(default="pool")
    id = HiddenField()
    name = StringField("Name", [InputRequired()])
    public = BooleanField("Public", default=False)
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
    manually_defined = BooleanField("Manually defined (won't be automatically updated)")


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
    action = "eNMS.inventory.exportTopology"
    form_type = HiddenField(default="excel_export")
    export_filename = StringField("Filename")
