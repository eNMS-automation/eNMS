from subprocess import check_output
from sqlalchemy import Boolean, ForeignKey, Integer
from wtforms import HiddenField

from eNMS.database.dialect import Column, LargeString, SmallString
from eNMS.forms.automation import ServiceForm
from eNMS.forms.fields import SubstitutionField
from eNMS.models.automation import Service


class UnixCommandService(Service):

    __tablename__ = "unix_command_service"

    id = Column(Integer, ForeignKey("service.id"), primary_key=True)
    command = Column(SmallString)

    __mapper_args__ = {"polymorphic_identity": "unix_command_service"}

    def job(self, run, payload, device):
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


class UnixCommandForm(ServiceForm):
    form_type = HiddenField(default="unix_command_service")
    command = SubstitutionField()
