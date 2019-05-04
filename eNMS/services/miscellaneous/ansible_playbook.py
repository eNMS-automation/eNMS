from json import dumps, loads
from json.decoder import JSONDecodeError
from sqlalchemy import Boolean, Column, ForeignKey, Integer, PickleType, String
from sqlalchemy.ext.mutable import MutableDict
from subprocess import check_output
from wtforms import BooleanField, HiddenField, SelectField, StringField
from wtforms.widgets import TextArea

from eNMS.forms import metaform
from eNMS.forms.automation import ServiceForm
from eNMS.forms.fields import DictField
from eNMS.models import register_class
from eNMS.models.automation import Service
from eNMS.models.inventory import Device


class AnsiblePlaybookService(Service, metaclass=register_class):

    __tablename__ = "AnsiblePlaybookService"

    id = Column(Integer, ForeignKey("Service.id"), primary_key=True)
    has_targets = Column(Boolean, default=False)
    playbook_path = Column(String(255), default="")
    arguments = Column(String(255), default="")
    validation_method = Column(String(255), default="")
    validation_method_values = (
        ("text", "Validation by text match"),
        ("dict_equal", "Validation by dictionary equality"),
        ("dict_included", "Validation by dictionary inclusion"),
    )
    content_match = Column(String(255), default="")
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


class AnsiblePlaybookForm(ServiceForm, metaclass=metaform):
    form_type = HiddenField(default="AnsiblePlaybookService")
    has_targets = BooleanField()
    playbook_path = StringField()
    arguments = StringField()
    validation_method = SelectField(
        choices=(
            ("text", "Validation by text match"),
            ("dict_equal", "Validation by dictionary equality"),
            ("dict_included", "Validation by dictionary inclusion"),
        )
    )
    content_match = StringField(widget=TextArea(), render_kw={"rows": 5})
    content_match_regex = BooleanField()
    dict_match = DictField()
    negative_logic = BooleanField()
    delete_spaces_before_matching = BooleanField()
    pass_device_properties = BooleanField()
    options = DictField()
