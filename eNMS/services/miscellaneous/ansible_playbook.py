from json import dumps
from sqlalchemy import Boolean, ForeignKey, Integer
from subprocess import check_output
from typing import Optional
from wtforms import BooleanField, HiddenField

from eNMS.controller import controller
from eNMS.database.dialect import Column, LargeString, MutableDict, SmallString
from eNMS.forms.automation import ServiceForm
from eNMS.forms.fields import (
    DictSubstitutionField,
    NoValidationSelectField,
    SubstitutionField,
)
from eNMS.forms.services import ValidationForm
from eNMS.models.automation import Run, Service
from eNMS.models.inventory import Device


class AnsiblePlaybookService(Service):

    __tablename__ = "AnsiblePlaybookService"

    id = Column(Integer, ForeignKey("Service.id"), primary_key=True)
    has_targets = Column(Boolean, default=False)
    playbook_path = Column(SmallString)
    arguments = Column(SmallString)
    conversion_method = Column(SmallString, default="text")
    validation_method = Column(SmallString)
    content_match = Column(LargeString, default="")
    content_match_regex = Column(Boolean, default=False)
    dict_match = Column(MutableDict)
    negative_logic = Column(Boolean, default=False)
    delete_spaces_before_matching = Column(Boolean, default=False)
    options = Column(MutableDict)
    pass_device_properties = Column(Boolean, default=False)

    __mapper_args__ = {"polymorphic_identity": "AnsiblePlaybookService"}

    def job(self, run: "Run", payload: dict, device: Optional[Device] = None) -> dict:
        arguments = run.sub(run.arguments, locals()).split()
        command, extra_args = ["ansible-playbook"], {}
        if run.pass_device_properties:
            extra_args = device.get_properties()
            extra_args.pop("configurations", None)
            extra_args.pop("current_configuration", None)
            extra_args["password"] = device.password
        if run.options:
            extra_args.update(run.sub(run.options, locals()))
        if extra_args:
            command.extend(["-e", dumps(extra_args)])
        if run.has_targets:
            command.extend(["-i", device.ip_address + ","])
        command.append(run.sub(run.playbook_path, locals()))
        run.log("info", f"Sending Ansible playbook: {' '.join(command + arguments)}")
        result = check_output(command + arguments, cwd=controller.path / "playbooks")
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
            "command": " ".join(command + arguments),
            "match": match,
            "negative_logic": run.negative_logic,
            "result": result,
            "success": run.match_content(result, match),
        }


class AnsiblePlaybookForm(ServiceForm, ValidationForm):
    form_type = HiddenField(default="AnsiblePlaybookService")
    has_targets = BooleanField("Has Target Devices")
    playbook_path = NoValidationSelectField("Playbook Path", choices=())
    arguments = SubstitutionField("Arguments (Ansible command line options)")
    pass_device_properties = BooleanField(
        "Pass Device Inventory Properties (to be used "
        "in the playbook as {{name}} or {{ip_address}})"
    )
    options = DictSubstitutionField("Options (passed to ansible as -e extra args)")
    groups = {
        "Main Parameters": [
            "has_targets",
            "playbook_path",
            "arguments",
            "pass_device_properties",
            "options",
        ],
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
