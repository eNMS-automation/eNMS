from sqlalchemy import (
    Boolean,
    Column,
    Float,
    ForeignKey,
    Integer,
    PickleType,
    String,
    Text,
)
from sqlalchemy.ext.mutable import MutableDict
from typing import Optional
from wtforms import (
    HiddenField,
    SelectField,
    StringField,
)

from eNMS.database import LARGE_STRING_LENGTH, SMALL_STRING_LENGTH
from eNMS.forms.automation import ServiceForm
from eNMS.forms.services import NetmikoForm, ValidationForm
from eNMS.models.automation import Job, Service
from eNMS.models.inventory import Device


class NetmikoValidationService(Service):

    __tablename__ = "NetmikoValidationService"

    id = Column(Integer, ForeignKey("Service.id"), primary_key=True)
    has_targets = True
    privileged_mode = Column(Boolean, default=False)
    command = Column(String(SMALL_STRING_LENGTH), default="")
    conversion_method = Column(String(SMALL_STRING_LENGTH), default="text")
    validation_method = Column(String(SMALL_STRING_LENGTH), default="text")
    content_match = Column(Text(LARGE_STRING_LENGTH), default="")
    content_match_regex = Column(Boolean, default=False)
    dict_match = Column(MutableDict.as_mutable(PickleType), default={})
    negative_logic = Column(Boolean, default=False)
    delete_spaces_before_matching = Column(Boolean, default=False)
    driver = Column(String(SMALL_STRING_LENGTH), default="")
    use_device_driver = Column(Boolean, default=True)
    fast_cli = Column(Boolean, default=False)
    timeout = Column(Integer, default=10.0)
    delay_factor = Column(Float, default=1.0)
    global_delay_factor = Column(Float, default=1.0)

    __mapper_args__ = {"polymorphic_identity": "NetmikoValidationService"}

    def job(self, payload: dict, device: Device, parent: Optional[Job] = None) -> dict:
        netmiko_connection = self.netmiko_connection(device, parent)
        command = self.sub(self.command, locals())
        self.logs.append(f"Sending '{command}' on {device.name} (Netmiko)")
        result = self.convert_result(
            netmiko_connection.send_command(command, delay_factor=self.delay_factor)
        )
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


class NetmikoValidationForm(ServiceForm, ValidationForm):
    form_type = HiddenField(default="NetmikoValidationService")
    command = StringField()
    conversion_method = SelectField(
        choices=(
            ("text", "Text"),
            ("json", "Json dictionary"),
            ("xml", "XML dictionary"),
        )
    )
    groups = {
        "Netmiko Parameters": NetmikoForm.group,
        "Validation Parameters": ValidationForm.group,
    }
