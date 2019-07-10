from json import dumps
from sqlalchemy import Boolean, Column, ForeignKey, Integer, PickleType, String, Text
from sqlalchemy.ext.mutable import MutableDict
from subprocess import check_output
from typing import Optional
from wtforms import BooleanField, HiddenField

from eNMS.database import LARGE_STRING_LENGTH, SMALL_STRING_LENGTH
from eNMS.forms.automation import ServiceForm
from eNMS.forms.fields import DictField, NoValidationSelectField, SubstitutionField
from eNMS.forms.services import ValidationForm
from eNMS.models.automation import Job, Service
from eNMS.models.inventory import Device


class AnsiblePlaybookService(Service):

    __tablename__ = "AnsiblePlaybookService"

    id = Column(Integer, ForeignKey("Service.id"), primary_key=True)
    has_targets = Column(Boolean, default=False)
    playbook_path = Column(String(SMALL_STRING_LENGTH), default="")
    arguments = Column(String(SMALL_STRING_LENGTH), default="")
    conversion_method = Column(String(SMALL_STRING_LENGTH), default="text")
    validation_method = Column(String(SMALL_STRING_LENGTH), default="")
    content_match = Column(Text(LARGE_STRING_LENGTH), default="")
    content_match_regex = Column(Boolean, default=False)
    dict_match = Column(MutableDict.as_mutable(PickleType), default={})
    negative_logic = Column(Boolean, default=False)
    delete_spaces_before_matching = Column(Boolean, default=False)
    options = Column(MutableDict.as_mutable(PickleType), default={})
    pass_device_properties = Column(Boolean, default=False)

    __mapper_args__ = {"polymorphic_identity": "AnsiblePlaybookService"}

    def job(
        self,
        payload: dict,
        device: Optional[Device] = None,
        parent: Optional[Job] = None,
    ) -> dict:
        arguments = self.sub(self.arguments, locals()).split()
        command, extra_args = ["ansible-playbook"], {}
        if self.pass_device_properties:
            extra_args = device.get_properties()
            extra_args["password"] = device.password
        if self.options:
            extra_args.update(self.options)
        if extra_args:
            command.extend(["-e", dumps(extra_args)])
        if self.has_targets:
            command.extend(["-i", device.ip_address + ","])
        command.append(self.sub(self.playbook_path, locals()))
        self.logs.append(f"Sending Ansible playbook: {' '.join(command + arguments)}")
        result = check_output(command + arguments)
        try:
            result = result.decode("utf-8")
        except AttributeError:
            pass
        result = self.convert_result(result)
        match = (
            self.sub(self.content_match, locals())
            if self.validation_method == "text"
            else self.sub(self.dict_match, locals())
        )
        return {
            "match": match,
            "negative_logic": self.negative_logic,
            "result": result,
            "success": self.match_content(result, match),
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
    options = DictField("Options (passed to ansible as -e extra args)")
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
        pass_properties_error = self.pass_device_properties.data and not self.has_targets.data
        if pass_properties_error:
            self.pass_device_properties.errors.append(
                "'pass device properties' requires 'has device targets' to be selected."
            )
        return valid_form and not pass_properties_error
