from subprocess import check_output
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text
from typing import Optional
from wtforms import HiddenField

from eNMS.database import LARGE_STRING_LENGTH, SMALL_STRING_LENGTH
from eNMS.forms.automation import ServiceForm
from eNMS.forms.fields import SubstitutionField
from eNMS.forms.services import ValidationForm
from eNMS.models.automation import Job, Service
from eNMS.models.inventory import Device


class UnixCommandService(Service):

    __tablename__ = "UnixCommandService"

    id = Column(Integer, ForeignKey("Service.id"), primary_key=True)
    has_targets = True
    command = Column(String(SMALL_STRING_LENGTH), default="")
    content_match = Column(Text(LARGE_STRING_LENGTH), default="")
    content_match_regex = Column(Boolean, default=False)
    negative_logic = Column(Boolean, default=False)
    delete_spaces_before_matching = Column(Boolean, default=False)

    __mapper_args__ = {"polymorphic_identity": "UnixCommandService"}

    def job(
        self,
        payload: dict,
        device: Optional[Device] = None,
        parent: Optional[Job] = None,
    ) -> dict:
        command = self.sub(self.command, locals())
        match = self.sub(self.content_match, locals())
        self.log(f"Running Unix command ({command}) on {device.name}")
        result = check_output(command.split()).decode()
        return {
            "success": self.match_content(result, match),
            "match": match,
            "negative_logic": self.negative_logic,
            "result": result,
        }


class UnixCommandForm(ServiceForm, ValidationForm):
    form_type = HiddenField(default="UnixCommandService")
    command = SubstitutionField()
