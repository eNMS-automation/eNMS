from sqlalchemy import Boolean, ForeignKey, Integer
from wtforms import HiddenField

from eNMS.database.dialect import Column, MutableDict, SmallString
from eNMS.forms.automation import ServiceForm
from eNMS.forms.services import NapalmForm
from eNMS.models.automation import Service
from eNMS.models.execution import Run
from eNMS.models.inventory import Device


class NapalmRollbackService(Service):

    __tablename__ = "NapalmRollbackService"

    id = Column(Integer, ForeignKey("service.id"), primary_key=True)
    has_targets = True
    driver = Column(SmallString)
    use_device_driver = Column(Boolean, default=True)
    optional_args = Column(MutableDict)

    __mapper_args__ = {"polymorphic_identity": "NapalmRollbackService"}

    def job(self, run: "Run", payload: dict, device: Device) -> dict:
        napalm_connection = run.napalm_connection(device)
        run.log("info", f"Configuration rollback on {device.name} (Napalm)")
        napalm_connection.rollback()
        return {"success": True, "result": "Rollback successful"}


class NapalmRollbackForm(ServiceForm, NapalmForm):
    form_type = HiddenField(default="NapalmRollbackService")
