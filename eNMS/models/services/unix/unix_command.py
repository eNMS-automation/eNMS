from subprocess import check_output
from sqlalchemy import Boolean, ForeignKey, Integer

from eNMS.database import db
from eNMS.forms import ServiceForm
from eNMS.fields import BooleanField, HiddenField, StringField
from eNMS.models.automation import Service


class UnixCommandService(Service):

    __tablename__ = "unix_command_service"
    pretty_name = "Unix Command"
    id = db.Column(Integer, ForeignKey("service.id"), primary_key=True)
    command = db.Column(db.SmallString)
    admin_approved = db.Column(Boolean, default=False)

    __mapper_args__ = {"polymorphic_identity": "unix_command_service"}

    def job(self, run, device=None):
        if not self.admin_approved:
            log = "This service must be approved by an Admin user first."
            run.log("error", log, device)
            return {"success": False, "result": log}
        command = run.sub(run.command, locals())
        run.log("info", f"Running UNIX command: {command}", device)
        return {"command": command, "result": check_output(command.split()).decode()}


class UnixCommandForm(ServiceForm):
    form_type = HiddenField(default="unix_command_service")
    command = StringField(substitution=True)
    admin_approved = BooleanField("Approved by an Admin user", default=False)
