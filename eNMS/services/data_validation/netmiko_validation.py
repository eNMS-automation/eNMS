from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, String, Text
from sqlalchemy.ext.mutable import MutableDict
from typing import Optional
from wtforms import BooleanField, HiddenField

from eNMS.database import (
    CustomMediumBlobPickle,
    LARGE_STRING_LENGTH,
    SMALL_STRING_LENGTH,
)
from eNMS.forms.automation import ServiceForm
from eNMS.forms.fields import SubstitutionField
from eNMS.forms.services import NetmikoForm, ValidationForm
from eNMS.models.automation import Job, Service
from eNMS.models.inventory import Device


class NetmikoValidationService(Service):

    __tablename__ = "NetmikoValidationService"

    id = Column(Integer, ForeignKey("Service.id"), primary_key=True)
    has_targets = True
    privileged_mode = Column(Boolean, default=False)
    command = Column(Text(LARGE_STRING_LENGTH), default="")
    conversion_method = Column(String(SMALL_STRING_LENGTH), default="text")
    validation_method = Column(String(SMALL_STRING_LENGTH), default="text")
    content_match = Column(Text(LARGE_STRING_LENGTH), default="")
    content_match_regex = Column(Boolean, default=False)
    dict_match = Column(MutableDict.as_mutable(CustomMediumBlobPickle), default={})
    negative_logic = Column(Boolean, default=False)
    delete_spaces_before_matching = Column(Boolean, default=False)
    driver = Column(String(SMALL_STRING_LENGTH), default="")
    use_device_driver = Column(Boolean, default=True)
    fast_cli = Column(Boolean, default=False)
    timeout = Column(Integer, default=10.0)
    delay_factor = Column(Float, default=1.0)
    global_delay_factor = Column(Float, default=1.0)
    expect_string = Column(String(SMALL_STRING_LENGTH), default="")
    auto_find_prompt = Column(Boolean, default=True)
    strip_prompt = Column(Boolean, default=True)
    strip_command = Column(Boolean, default=True)

    __mapper_args__ = {"polymorphic_identity": "NetmikoValidationService"}

    def job(self, run: "Run", device: Device) -> dict:
        netmiko_connection = self.netmiko_connection(device, run.workflow)
        command = self.sub(self.command, locals())
        run.log("info", f"Sending '{command}' on {device.name} (Netmiko)")
        expect_string = self.sub(self.expect_string, locals())
        result = self.convert_result(
            netmiko_connection.send_command(
                command,
                delay_factor=self.delay_factor,
                expect_string=self.expect_string or None,
                auto_find_prompt=self.auto_find_prompt,
                strip_prompt=self.strip_prompt,
                strip_command=self.strip_command,
            )
        )
        match = (
            self.sub(self.content_match, locals())
            if self.validation_method == "text"
            else self.sub(self.dict_match, locals())
        )
        return {
            "command": command,
            "match": match,
            "negative_logic": self.negative_logic,
            "result": result,
            "success": self.match_content(result, match),
        }


class NetmikoValidationForm(ServiceForm, NetmikoForm, ValidationForm):
    form_type = HiddenField(default="NetmikoValidationService")
    command = SubstitutionField()
    expect_string = SubstitutionField()
    auto_find_prompt = BooleanField(default=True)
    strip_prompt = BooleanField(default=True)
    strip_command = BooleanField(default=True)
    groups = {
        "Main Parameters": [
            "command",
            "expect_string",
            "auto_find_prompt",
            "strip_prompt",
            "strip_command",
        ],
        "Netmiko Parameters": NetmikoForm.group,
        "Validation Parameters": ValidationForm.group,
    }
