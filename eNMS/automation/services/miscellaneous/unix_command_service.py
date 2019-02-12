from subprocess import check_output
from sqlalchemy import Column, ForeignKey, Integer, String
from typing import overload

from eNMS.automation.models import Service
from eNMS.base.classes import service_classes
from eNMS.inventory.models import Device


class UnixCommandService(Service):

    __tablename__ = "UnixCommandService"

    id = Column(Integer, ForeignKey("Service.id"), primary_key=True)
    command = Column(String)

    __mapper_args__ = {"polymorphic_identity": "UnixCommandService"}

    @overload
    def job(self, payload: dict) -> dict:
        ...

    @overload  # noqa: F811
    def job(self, device: Device, payload: dict) -> dict:
        ...

    def job(self, *args):  # noqa: F811
        if len(args) == 2:
            device, payload = args
        try:
            command = self.sub(self.command, locals())
            return {"success": True, "result": check_output(command.split()).decode()}
        except Exception as e:
            return {"success": False, "result": str(e)}


service_classes["UnixCommandService"] = UnixCommandService
