from flask_login import current_user
from subprocess import check_output
from sqlalchemy import ForeignKey, Integer

from eNMS.database import db
from eNMS.forms import ServiceForm
from eNMS.fields import HiddenField, StringField
from eNMS.models.automation import Service


class UnixCommandService(Service):

    __tablename__ = "unix_command_service"
    pretty_name = "Unix Command"
    id = db.Column(Integer, ForeignKey("service.id"), primary_key=True)
    command = db.Column(db.SmallString)

    __mapper_args__ = {"polymorphic_identity": "unix_command_service"}

    def job(self, run, device=None):
        command = run.sub(run.command, locals())
        run.log("info", f"Running UNIX command: {command}", device)
        result = check_output(command, shell=True).decode()
        return {"command": command, "result": result}


class UnixCommandForm(ServiceForm):
    form_type = HiddenField(default="unix_command_service")
    command = StringField(substitution=True)

    def validate(self):
        valid_form = super().validate()
        if not self.id.data:
            return valid_form
        current_command = db.fetch("service", id=self.id.data).command
        rbac_error = not current_user.is_admin and self.command.data != current_command
        if rbac_error:
            error_message = "Only an admin user can change the Unix command."
            self.command.errors.append(error_message)
        return valid_form and not rbac_error
