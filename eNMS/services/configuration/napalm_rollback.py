from sqlalchemy import Boolean, Column, ForeignKey, Integer, PickleType, String
from sqlalchemy.ext.mutable import MutableDict
from wtforms import BooleanField, HiddenField, SelectField

from eNMS.controller import controller
from eNMS.database import SMALL_STRING_LENGTH
from eNMS.forms import metaform
from eNMS.forms.automation import ServiceForm
from eNMS.forms.fields import DictField
from eNMS.models import register_class
from eNMS.models.automation import Service
from eNMS.models.inventory import Device


class NapalmRollbackService(Service, metaclass=register_class):

    __tablename__ = "NapalmRollbackService"

    id = Column(Integer, ForeignKey("Service.id"), primary_key=True)
    has_targets = True
    driver = Column(String(SMALL_STRING_LENGTH), default="")
    use_device_driver = Column(Boolean, default=True)
    optional_args = Column(MutableDict.as_mutable(PickleType), default={})

    __mapper_args__ = {"polymorphic_identity": "NapalmRollbackService"}

    def job(self, payload: dict, device: Device) -> dict:
        napalm_driver = self.napalm_connection(device)
        napalm_driver.open()
        self.logs.append(f"Configuration rollback on {device.name} (Napalm)")
        napalm_driver.rollback()
        napalm_driver.close()
        return {"success": True, "result": "Rollback successful"}


class NapalmRollbackForm(ServiceForm, metaclass=metaform):
    form_type = HiddenField(default="NapalmRollbackService")
    driver = SelectField(choices=controller.NAPALM_DRIVERS)
    use_device_driver = BooleanField(default=True)
    optional_args = DictField()
