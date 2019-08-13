from subprocess import check_output
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text
from wtforms import HiddenField

from eNMS.database import LARGE_STRING_LENGTH, SMALL_STRING_LENGTH
from eNMS.forms.automation import ServiceForm
from eNMS.forms.fields import SubstitutionField
from eNMS.forms.services import ValidationForm
from eNMS.models.automation import Run, Service
from eNMS.models.inventory import Device


class UnixCommandService(Service):

    __tablename__ = "UnixCommandService"

    id = Column(Integer, ForeignKey("Service.id"), primary_key=True)
    has_targets = True
    command = Column(SmallString, default="")
    content_match = Column(LargeString, default="")
    content_match_regex = Column(Boolean, default=False)
    negative_logic = Column(Boolean, default=False)
    delete_spaces_before_matching = Column(Boolean, default=False)

    __mapper_args__ = {"polymorphic_identity": "UnixCommandService"}

    def job(self, run: "Run", payload: dict, device: Device) -> dict:
        command = run.sub(run.command, locals())
        match = run.sub(run.content_match, locals())
        run.log("info", f"Running Unix command ({command}) on {device.name}")
        result = check_output(command.split()).decode()
        return {
            "success": run.match_content(result, match),
            "match": match,
            "negative_logic": run.negative_logic,
            "result": result,
        }


class UnixCommandForm(ServiceForm, ValidationForm):
    form_type = HiddenField(default="UnixCommandService")
    command = SubstitutionField()
