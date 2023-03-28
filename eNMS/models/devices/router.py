from sqlalchemy import ForeignKey, Integer

from eNMS.database import db
from eNMS.forms import DeviceForm
from eNMS.fields import HiddenField, StringField
from eNMS.models.inventory import Device


class Router(Device):
    __tablename__ = "router"
    __mapper_args__ = {"polymorphic_identity": "router"}
    pretty_name = "Router"
    id = db.Column(Integer, ForeignKey("device.id"), primary_key=True)
    serial_number = db.Column(db.SmallString)


class RouterForm(DeviceForm):
    form_type = HiddenField(default="router")
    serial_number = StringField("Serial Number")
    properties = ["serial_number"]
