from subprocess import check_output
from sqlalchemy import ForeignKey, Integer
from wtforms import HiddenField

from eNMS.database.dialect import Column, SmallString
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
        run.log("info", f"Running Unix command ({command}) on {device.name}")
        return {"command": command, "result": check_output(command.split()).decode()}


class UnixCommandForm(ServiceForm):
    form_type = HiddenField(default="unix_command_service")
    command = SubstitutionField()
