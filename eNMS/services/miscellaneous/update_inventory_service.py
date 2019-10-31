from sqlalchemy import ForeignKey, Integer
from wtforms import HiddenField

from eNMS.database.dialect import Column, MutableDict
from eNMS.forms.automation import ServiceForm
from eNMS.forms.fields import DictField
from eNMS.models.automation import Service


class UpdateInventoryService(Service):

    __tablename__ = "update_inventory_service"
    pretty_name = "Update Inventory"
    id = Column(Integer, ForeignKey("service.id"), primary_key=True)
    update_dictionary = Column(MutableDict)

    __mapper_args__ = {"polymorphic_identity": "update_inventory_service"}

    def job(self, run, payload, device):
        for property, value in run.update_dictionary.items():
            setattr(device, property, value)
        return {"success": True, "result": "properties updated"}


class UpdateInventoryForm(ServiceForm):
    form_type = HiddenField(default="update_inventory_service")
    update_dictionary = DictField()
