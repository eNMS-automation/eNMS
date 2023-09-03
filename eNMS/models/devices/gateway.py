from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import relationship

from eNMS.database import db, vs
from eNMS.fields import MultipleInstanceField
from eNMS.forms import DeviceForm
from eNMS.fields import HiddenField, IntegerField, SelectField
from eNMS.models.inventory import Device


class Gateway(Device):
    __tablename__ = "gateway"
    __mapper_args__ = {"polymorphic_identity": "gateway"}
    pretty_name = "Gateway"
    id = db.Column(Integer, ForeignKey("device.id"), primary_key=True)
    priority = db.Column(Integer, default=1)
    devices = relationship(
        "Device", secondary=db.device_gateway_table, back_populates="gateways"
    )


class GatewayForm(DeviceForm):
    form_type = HiddenField(default="gateway")
    icon = SelectField(
        "Icon", choices=list(vs.visualization["icons"].items()), default="host"
    )
    priority = IntegerField("Priority", default=1)
    devices = MultipleInstanceField("Devices", model="device")
    properties = ["priority", "devices"]
