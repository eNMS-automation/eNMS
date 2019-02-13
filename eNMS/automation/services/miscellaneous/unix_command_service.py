from subprocess import check_output
from sqlalchemy import Column, ForeignKey, Integer, String
from typing import Optional

from eNMS.automation.models import Service
from eNMS.base.classes import service_classes
from eNMS.inventory.models import Device


class UnixCommandService(Service):

    __tablename__ = "UnixCommandService"

    id = Column(Integer, ForeignKey("Service.id"), primary_key=True)
    command = Column(String)

    __mapper_args__ = {"polymorphic_identity": "UnixCommandService"}

    def job(self, payload: dict, device: Optional[Device] = None) -> dict:
        try:
            command = self.sub(self.command, locals())
            return {"success": True, "result": check_output(command.split()).decode()}
        except Exception as e:
            return {"success": False, "result": str(e)}


service_classes["UnixCommandService"] = UnixCommandService
