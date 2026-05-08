from flask_login import current_user
from sqlalchemy import Boolean, ForeignKey, Integer
from subprocess import run as sub_run

from eNMS.database import db
from eNMS.fields import BooleanField, HiddenField, StringField
from eNMS.forms import ServiceForm
from eNMS.models.automation import Service


class UnixCommandService(Service):
    __tablename__ = "unix_command_service"
    pretty_name = "Unix Command"
    id = db.Column(Integer, ForeignKey("service.id"), primary_key=True)
    command = db.Column(db.SmallString)
    approved_by_admin = db.Column(Boolean, default=False)

    __mapper_args__ = {"polymorphic_identity": "unix_command_service"}

    def update(self, **kwargs):
        if not getattr(current_user, "is_admin", True):
            kwargs["approved_by_admin"] = False
        super().update(**kwargs)

    @staticmethod
    def job(self, run, device=None):
        command = run.sub(run.command, locals())
        log_command = run.safe_log(run.command, command)
        if run.dry_run:
            return {"command": log_command}
        if not self.approved_by_admin:
            log = "The service has not been approved by an admin user."
            run.log("error", log, device)
            return {"success": False, "result": log}
        run.log("info", f"Running UNIX command: {log_command}", device)
        result = sub_run(command, shell=True, capture_output=True, text=True)
        return {
            "command": log_command,
            "result": result.stdout or result.stderr,
            "return_code": result.returncode,
            "success": result.returncode == 0,
        }


class UnixCommandForm(ServiceForm):
    form_type = HiddenField(default="unix_command_service")
    command = StringField(substitution=True)
    approved_by_admin = BooleanField("Approved by an admin user", default=False)

    def validate(self, **_):
        valid_form = super().validate()
        rbac_error = self.approved_by_admin.data and not current_user.is_admin
        if rbac_error:
            self.approved_by_admin.errors.append(
                "Only an admin user can save when 'Approved"
                " by an admin user' is selected."
            )
        return valid_form and not rbac_error
