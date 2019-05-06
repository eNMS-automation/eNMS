from json import dumps, loads
from json.decoder import JSONDecodeError
from sqlalchemy import Boolean, Column, ForeignKey, Integer, PickleType, String, Text
from sqlalchemy.ext.mutable import MutableDict
from subprocess import check_output
from wtforms import BooleanField, HiddenField, StringField

from eNMS.database import LARGE_STRING_LENGTH, SMALL_STRING_LENGTH
from eNMS.forms.automation import ServiceForm
from eNMS.forms.fields import DictField
from eNMS.forms.services import ValidationForm
from eNMS.models.automation import Service
from eNMS.models.inventory import Device


class AnsiblePlaybookService(Service):

    __tablename__ = "AnsiblePlaybookService"

    id = Column(Integer, ForeignKey("Service.id"), primary_key=True)
    has_targets = Column(Boolean, default=False)
    playbook_path = Column(String(SMALL_STRING_LENGTH), default="")
    arguments = Column(String(SMALL_STRING_LENGTH), default="")
    validation_method = Column(String(SMALL_STRING_LENGTH), default="")
    content_match = Column(Text(LARGE_STRING_LENGTH), default="")
    content_match_regex = Column(Boolean, default=False)
    dict_match = Column(MutableDict.as_mutable(PickleType), default={})
    negative_logic = Column(Boolean, default=False)
    delete_spaces_before_matching = Column(Boolean, default=False)
    options = Column(MutableDict.as_mutable(PickleType), default={})
    pass_device_properties = Column(Boolean, default=False)

    __mapper_args__ = {"polymorphic_identity": "AnsiblePlaybookService"}

    def job(self, payload: dict, device: Device) -> dict:
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
        try:
            result = loads(result)
        except JSONDecodeError:
            pass
        if self.validation_method == "text":
            success = self.match_content(
                str(result), self.sub(self.content_match, locals())
            )
        else:
            success = self.match_dictionary(result)
        return {
            "negative_logic": self.negative_logic,
            "result": result,
            "success": success,
        }


class AnsiblePlaybookForm(ServiceForm, ValidationForm):
    form_type = HiddenField(default="AnsiblePlaybookService")
    has_targets = BooleanField()
    playbook_path = StringField()
    arguments = StringField()
    pass_device_properties = BooleanField()
    options = DictField()
