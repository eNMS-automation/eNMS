from wtforms.validators import InputRequired
from wtforms.widgets import TextArea

from eNMS import app
from eNMS.forms import BaseForm, choices, form_properties
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
    action = "eNMS.base.processData"
    form_type = HiddenField(default="object")
    id = HiddenField()
    name = StringField("Name", [InputRequired()])
    default_access = SelectField(
        choices=(
            ("creator", "Creator only"),
            ("public", "Public (all users)"),
            ("admin", "Admin Users only"),
        )
    )
    access_groups = StringField("Groups")
    description = StringField("Description")
    subtype = StringField("Subtype")
    location = StringField("Location")
    vendor = StringField("Vendor")
    model = StringField("Model")


class DeviceForm(ObjectForm):
    form_type = HiddenField(default="device")
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
    action = "eNMS.base.processData"
    form_type = HiddenField(default="link")
    source = InstanceField("Source", [InputRequired()], model="device")
    destination = InstanceField("Destination", [InputRequired()], model="device")
    color = StringField("Color")


class PoolForm(BaseForm):
    template = "pool"
    form_type = HiddenField(default="pool")
    id = HiddenField()
    name = StringField("Name", [InputRequired()])
    default_access = SelectField(
        choices=(
            ("creator", "Creator only"),
            ("public", "Public (all users)"),
            ("admin", "Admin Users only"),
        )
    )
    access_groups = StringField("Groups")
    description = StringField("Description")
    operator = SelectField(
        "Type of match",
        choices=(
            ("all", "Match if all properties match"),
            ("any", "Match if any property matches"),
        ),
    )
    manually_defined = BooleanField("Manually defined (won't be automatically updated)")

    @classmethod
    def form_init(cls):
        cls.models = ("device", "link", "service", "user")
        for model in cls.models:
            setattr(cls, f"{model}_properties", app.properties["filtering"][model])
            for property in app.properties["filtering"][model]:
                setattr(cls, f"{model}_{property}", StringField(property))
                setattr(cls, f"{model}_{property}_invert", BooleanField(property))
                form_properties["pool"][f"{model}_{property}_invert"] = {"type": "bool"}
                setattr(
                    cls,
                    f"{model}_{property}_match",
                    SelectField(
                        choices=(
                            ("inclusion", "Inclusion"),
                            ("equality", "Equality"),
                            ("regex", "Regular Expression"),
                        )
                    ),
                )


class ExcelImportForm(BaseForm):
    template = "topology_import"
    form_type = HiddenField(default="excel_import")
    replace = BooleanField("Replace Existing Topology")


class ExportForm(BaseForm):
    action = "eNMS.inventory.exportTopology"
    form_type = HiddenField(default="excel_export")
    export_filename = StringField("Filename")


class VisualizationForm(BaseForm):
    action = "eNMS.visualization.saveParameters"
    form_type = HiddenField(default="visualization_parameters")
    default_pools = MultipleInstanceField("Pools", model="pool")


class LogicalViewForm(BaseForm):
    action = "eNMS.base.processData"
    form_type = HiddenField(default="view")
    id = HiddenField()
    name = StringField("Name", [InputRequired()])


class ViewLabelForm(BaseForm):
    form_type = HiddenField(default="view_label")
    action = "eNMS.visualization.createLabel"
    text = StringField(widget=TextArea(), render_kw={"rows": 15})


class ViewLabelForm(BaseForm):
    form_type = HiddenField(default="view_plan")
    action = "eNMS.visualization.createPlan"
    size = IntegerField("Grid Size", default=2000)
    rows = IntegerField("Grid Rows", default=100)


class AddObjectsForm(BaseForm):
    form_type = HiddenField(default="add_objects_to_view")
    action = "eNMS.visualization.addObjectsToView"
    devices = MultipleInstanceField("Devices", model="device")
    links = MultipleInstanceField("Links", model="link")
