from subprocess import check_output
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from typing import Optional

from eNMS.automation.models import Service
from eNMS.classes import service_classes
from eNMS.inventory.models import Device


class UnixCommandService(Service):

    __tablename__ = "UnixCommandService"

    id = Column(Integer, ForeignKey("Service.id"), primary_key=True)
    command = Column(String(255))
    content_match = Column(String(255))
    content_match_textarea = True
    content_match_regex = Column(Boolean)
    negative_logic = Column(Boolean)
    delete_spaces_before_matching = Column(Boolean)

    __mapper_args__ = {"polymorphic_identity": "UnixCommandService"}

    def job(self, payload: dict, device: Optional[Device] = None) -> dict:
        command = self.sub(self.command, locals())
        match = self.sub(self.content_match, locals())
        self.logs.append(f"Running Unix command ({command}) on {device.name}")
        result = check_output(command.split()).decode()
        return {
            "success": self.match_content(result, match),
            "match": match,
            "negative_logic": self.negative_logic,
            "result": result,
        }


service_classes["UnixCommandService"] = UnixCommandService
