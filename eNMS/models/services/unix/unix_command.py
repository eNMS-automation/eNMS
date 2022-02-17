from flask_login import current_user
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

    def validate(self):
        valid_form = super().validate()
        admin_approved_error = not current_user.is_admin and self.admin_approved.data
        if admin_approved_error:
            self.admin_approved.errors.append(
                (
                    "You must untick the 'Approved by an Admin user'" 
                    " box to be allowed to save that service."
                )
            )
        return valid_form and not admin_approved_error
