from json import dumps
from re import search
from sqlalchemy import Boolean, ForeignKey, Integer
from subprocess import check_output
from traceback import format_exc

from eNMS import app
from eNMS.database import db
from eNMS.forms.automation import ServiceForm
from eNMS.forms.fields import (
    BooleanField,
    DictField,
    HiddenField,
    SelectField,
    StringField,
)
from eNMS.models.automation import Service


class AnsiblePlaybookService(Service):

    __tablename__ = "ansible_playbook_service"
    pretty_name = "Ansible Playbook"
    id = db.Column(Integer, ForeignKey("service.id"), primary_key=True)
    playbook_path = db.Column(db.SmallString)
    arguments = db.Column(db.SmallString)
    options = db.Column(db.Dict)
    pass_device_properties = db.Column(Boolean, default=False)

    exit_codes = {
        "0": "OK or no hosts matched",
        "1": "Error",
        "2": "One or more hosts failed",
        "3": "One or more hosts were unreachable",
        "4": "Parser error",
        "5": "Bad or incomplete options",
        "99": "User interrupted execution",
        "250": "Unexpected error",
    }

    __mapper_args__ = {"polymorphic_identity": "ansible_playbook_service"}

    def job(self, run, payload, device=None):
        arguments = run.sub(run.arguments, locals()).split()
        command, extra_args = ["ansible-playbook"], {}
        if run.pass_device_properties:
            extra_args = device.get_properties()
            extra_args["password"] = app.get_password(device.password)
        if run.options:
            extra_args.update(run.sub(run.options, locals()))
        if extra_args:
            command.extend(["-e", dumps(extra_args)])
        if device:
            command.extend(["-i", device.ip_address + ","])
        command.append(run.sub(run.playbook_path, locals()))
        password = extra_args.get("password")
        full_command = " ".join(command + arguments)
        if password:
            full_command = full_command.replace(password, "*" * 10)
        run.log(
            "info",
            f"Sending Ansible playbook: {full_command}",
            device,
            logger="security",
        )
        try:
            result = check_output(
                command + arguments, cwd=app.path / "files" / "playbooks"
            )
        except Exception:
            result = "\n".join(format_exc().splitlines())
            if password:
                result = result.replace(password, "*" * 10)
            results = {"success": False, "result": result, "command": full_command}
            exit_code = search(r"exit status (\d+)", result)
            if exit_code:
                results["exit_code"] = self.exit_codes[exit_code.group(1)]
            return results
        try:
            result = result.decode("utf-8")
        except AttributeError:
            pass
        return {"command": full_command, "result": result}


class AnsiblePlaybookForm(ServiceForm):
    form_type = HiddenField(default="ansible_playbook_service")
    playbook_path = SelectField("Playbook Path", choices=(), validation=False)
    arguments = StringField(
        "Arguments (Ansible command line options)",
        substitution=True,
        render_kw={"help": "ansible/arguments"},
    )
    pass_device_properties = BooleanField(
        "Pass Device Inventory Properties (to be used "
        "in the playbook as {{name}} or {{ip_address}})"
    )
    options = DictField(
        "Options (passed to ansible as -e extra args)",
        substitution=True,
        render_kw={"help": "ansible/options"},
    )
