from eNMS.forms import BaseForm
from eNMS.forms.fields import (
    BooleanField,
    HiddenField,
    IntegerField,
    MultipleInstanceField,
    PasswordField,
    SelectField,
    StringField,
)


class CustomForm(BaseForm):
    form_type = HiddenField(default="custom")
    address = SelectField(choices=[("ipv4", "IPv4"), ("ipv6", "IPv6")])
    connected_links = MultipleInstanceField("Links", model="link")
    hostname = StringField("Username", default="admin")
    ip_address = StringField("IP address")
    neighbors = MultipleInstanceField("Devices", model="device")
    password = PasswordField("Password")
    router_id = IntegerField("Router ID")
    carry_customer_traffic = BooleanField("Carry Customer Traffic", default=False)


class PanelForm(BaseForm):
    form_type = HiddenField(default="panel")
    action = "eNMS.plugins.submitPanelForm"
    ip_address = StringField("IP address")
    router_id = IntegerField("Router ID")
