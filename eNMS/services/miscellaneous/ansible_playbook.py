from json import dumps
from re import search
from sqlalchemy import Boolean, ForeignKey, Integer
from subprocess import check_output
from traceback import format_exc
from typing import Optional
from wtforms import BooleanField, HiddenField

from eNMS import app
from eNMS.database.dialect import Column, LargeString, MutableDict, SmallString
from eNMS.forms.automation import ServiceForm
from eNMS.forms.fields import (
    DictSubstitutionField,
    NoValidationSelectField,
    SubstitutionField,
)
from eNMS.forms.services import ValidationForm
from eNMS.models.automation import Service
from eNMS.models.execution import Run
from eNMS.models.inventory import Device


class AnsiblePlaybookService(Service):

    __tablename__ = "ansible_playbook_service"

    id = Column(Integer, ForeignKey("service.id"), primary_key=True)
    has_targets = Column(Boolean, default=False)
    playbook_path = Column(SmallString)
    arguments = Column(SmallString)
    conversion_method = Column(SmallString, default="none")
    validation_method = Column(SmallString)
    content_match = Column(LargeString, default="")
    content_match_regex = Column(Boolean, default=False)
    dict_match = Column(MutableDict)
    negative_logic = Column(Boolean, default=False)
    delete_spaces_before_matching = Column(Boolean, default=False)
    options = Column(MutableDict)
    pass_device_properties = Column(Boolean, default=False)

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

    def job(self, run: "Run", payload: dict, device: Optional[Device] = None) -> dict:
        arguments = run.sub(run.arguments, locals()).split()
        command, extra_args = ["ansible-playbook"], {}
        if run.pass_device_properties:
            extra_args = device.get_properties()
            extra_args["password"] = device.password
        if run.options:
            extra_args.update(run.sub(run.options, locals()))
        if extra_args:
            command.extend(["-e", dumps(extra_args)])
        if run.has_targets:
            command.extend(["-i", device.ip_address + ","])
        command.append(run.sub(run.playbook_path, locals()))
        password = extra_args.get("password")
        if password:
            safe_command = " ".join(command + arguments).replace(password, "*" * 10)
        run.log("info", f"Sending Ansible playbook: {safe_command}")
        try:
            result = check_output(command + arguments, cwd=app.path / "playbooks")
        except Exception:
            result = "\n".join(format_exc().splitlines())
            if password:
                result = result.replace(password, "*" * 10)
            results = {"success": False, "results": result}
            exit_code = search(r"exit status (\d+)", result)
            if exit_code:
                results["exit_code"] = self.exit_codes[exit_code.group(1)]
            return results
        try:
            result = result.decode("utf-8")
        except AttributeError:
            pass
        result = run.convert_result(result)
        match = (
            run.sub(run.content_match, locals())
            if run.validation_method == "text"
            else run.sub(run.dict_match, locals())
        )
        return {
            "command": safe_command,
            "match": match,
            "negative_logic": run.negative_logic,
            "result": result,
            "success": run.match_content(result, match),
        }


class AnsiblePlaybookForm(ServiceForm, ValidationForm):
    form_type = HiddenField(default="ansible_playbook_service")
    has_targets = BooleanField("Has Target Devices", default=True)
    playbook_path = NoValidationSelectField("Playbook Path", choices=())
    arguments = SubstitutionField("Arguments (Ansible command line options)")
    pass_device_properties = BooleanField(
        "Pass Device Inventory Properties (to be used "
        "in the playbook as {{name}} or {{ip_address}})"
    )
    options = DictSubstitutionField("Options (passed to ansible as -e extra args)")
    groups = {
        "Main Parameters": {
            "commands": [
                "has_targets",
                "playbook_path",
                "arguments",
                "pass_device_properties",
                "options",
            ],
            "default": "expanded",
        },
        "Validation Parameters": ValidationForm.group,
    }

    def validate(self) -> bool:
        valid_form = super().validate()
        pass_properties_error = (
            self.pass_device_properties.data and not self.has_targets.data
        )
        if pass_properties_error:
            self.pass_device_properties.errors.append(
                "'pass device properties' requires 'has device targets' to be selected."
            )
        return valid_form and not pass_properties_error
