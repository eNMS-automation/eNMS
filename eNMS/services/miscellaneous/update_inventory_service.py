from sqlalchemy import Column, ForeignKey, Integer, PickleType
from sqlalchemy.ext.mutable import MutableDict
from typing import Optional
from wtforms import HiddenField

from eNMS.forms.automation import ServiceForm
from eNMS.forms.fields import DictField
from eNMS.models.automation import Job, Service
from eNMS.models.inventory import Device


class UpdateInventoryService(Service):

    __tablename__ = "UpdateInventoryService"

    id = Column(Integer, ForeignKey("Service.id"), primary_key=True)
    has_targets = True
    update_dictionary = Column(MutableDict.as_mutable(PickleType), default={})

    __mapper_args__ = {"polymorphic_identity": "UpdateInventoryService"}

    def job(
        self,
        payload: dict,
        timestamp: str,
        device: Device,
        parent: Optional[Job] = None,
    ) -> dict:
        for property, value in self.update_dictionary.items():
            setattr(device, property, value)
        return {"success": True, "result": "properties updated"}


class UpdateInventoryForm(ServiceForm):
    form_type = HiddenField(default="UpdateInventoryService")
    update_dictionary = DictField()
