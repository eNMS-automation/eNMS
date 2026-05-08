from sqlalchemy import Boolean, ForeignKey, Integer
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import relationship

from eNMS.database import db
from eNMS.fields import (
    BooleanField,
    HiddenField,
    InstanceField,
    SelectField,
    StringField,
)
from eNMS.forms import DataForm
from eNMS.models.administration import Data


class Port(Data):
    __tablename__ = "port"
    pretty_name = "Port"
    __mapper_args__ = {"polymorphic_identity": "port"}
    id = db.Column(Integer, ForeignKey("data.id"), primary_key=True)
    label = db.Column(db.SmallString)
    speed = db.Column(db.SmallString)
    connected = db.Column(Boolean, default=False)
    device_id = db.Column(Integer, ForeignKey("device.id"))
    device = relationship("Device", backref="ports")
    device_name = association_proxy("device", "name")


class PortForm(DataForm):
    form_type = HiddenField(default="port")
    store = InstanceField("Store", model="store", constraints={"data_type": "port"})
    device = InstanceField("Device", model="device")
    label = StringField()
    speed = SelectField(choices=("10BASE-T", "100BASE-T", "1000BASE-T", "10GBASE-T"))
    connected = BooleanField("Connected", default=False)
    properties = ["device", "label", "speed", "connected"]
