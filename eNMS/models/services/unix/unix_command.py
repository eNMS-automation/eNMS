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
    approved_by_admin = db.Column(Boolean, default=False)

    __mapper_args__ = {"polymorphic_identity": "unix_command_service"}

    def job(self, run, device=None):
        if not self.approved_by_admin:
            log = "The service has not been approved by an admin user."
            run.log("error", log, device)
            return {"success": False, "result": log}
        command = run.sub(run.command, locals())
        run.log("info", f"Running UNIX command: {command}", device)
        result = check_output(command, shell=True).decode()
        return {"command": command, "result": result}


class UnixCommandForm(ServiceForm):
    form_type = HiddenField(default="unix_command_service")
    command = StringField(substitution=True)
    approved_by_admin = BooleanField("Approved by an admin user", default=False)

    def validate(self):
        valid_form = super().validate()
        service = db.fetch("service", id=self.id.data, allow_none=True)
        current_command = getattr(service, "command", "")
        current_approval = getattr(service, "approved_by_admin", False)
        check_rbac = self.approved_by_admin.data and not current_user.is_admin
        approved_by_admin_error = check_rbac and not current_approval
        if approved_by_admin_error:
            error_message = "A non-admin user cannot approve the Unix command."
            self.approved_by_admin.errors.append(error_message)
        command_error = check_rbac and self.command.data != current_command
        if command_error:
            error_message = "The command must be approved by an admin user."
            self.approved_by_admin.errors.append(error_message)
        return valid_form and not command_error and not approved_by_admin_error
