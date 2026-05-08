from sqlalchemy import ForeignKey, Integer

from eNMS.database import db
from eNMS.fields import HiddenField
from eNMS.forms import DeviceForm
from eNMS.models.inventory import Device


class GenericDevice(Device):
    __tablename__ = "generic_device"
    __mapper_args__ = {"polymorphic_identity": "generic_device"}
    pretty_name = "Generic Device"
    id = db.Column(Integer, ForeignKey("device.id"), primary_key=True)


class GenericDeviceForm(DeviceForm):
    form_type = HiddenField(default="generic_device")
