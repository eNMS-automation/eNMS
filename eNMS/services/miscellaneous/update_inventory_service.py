from sqlalchemy import ForeignKey, Integer
from wtforms import HiddenField

from eNMS.database.dialect import Column, MutableDict
from eNMS.forms.automation import ServiceForm
from eNMS.forms.fields import DictField
from eNMS.models.automation import Service
from eNMS.models.execution import Run
from eNMS.models.inventory import Device


class UpdateInventoryService(Service):

    __tablename__ = "update_inventory_service"

    id = Column(Integer, ForeignKey("service.id"), primary_key=True)
    has_targets = True
    update_dictionary = Column(MutableDict)

    __mapper_args__ = {"polymorphic_identity": "update_inventory_service"}

    def job(self, run: "Run", payload, device: Device) -> dict:
        for property, value in run.update_dictionary.items():
            setattr(device, property, value)
        return {"success": True, "result": "properties updated"}


class UpdateInventoryForm(ServiceForm):
    form_type = HiddenField(default="update_inventory_service")
    update_dictionary = DictField()
