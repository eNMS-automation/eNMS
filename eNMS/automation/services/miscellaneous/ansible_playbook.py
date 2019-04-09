from json import dumps, loads
from json.decoder import JSONDecodeError
from sqlalchemy import Boolean, Column, ForeignKey, Integer, PickleType, String
from sqlalchemy.ext.mutable import MutableDict
from subprocess import check_output

from eNMS.automation.models import Service
from eNMS.classes import service_classes
from eNMS.inventory.models import Device


class AnsiblePlaybookService(Service):

    __tablename__ = "AnsiblePlaybookService"

    id = Column(Integer, ForeignKey("Service.id"), primary_key=True)
    has_targets = Column(Boolean)
    playbook_path = Column(String(255))
    arguments = Column(String(255))
    validation_method = Column(String(255))
    validation_method_values = (
        ("text", "Validation by text match"),
        ("dict_equal", "Validation by dictionary equality"),
        ("dict_included", "Validation by dictionary inclusion"),
    )
    content_match = Column(String(255))
    content_match_textarea = True
    content_match_regex = Column(Boolean)
    dict_match = Column(MutableDict.as_mutable(PickleType), default={})
    negative_logic = Column(Boolean)
    delete_spaces_before_matching = Column(Boolean)
    options = Column(MutableDict.as_mutable(PickleType), default={})
    pass_device_properties = Column(Boolean)

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


service_classes["AnsiblePlaybookService"] = AnsiblePlaybookService
