from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, String, Text
from sqlalchemy.ext.mutable import MutableDict
from wtforms import BooleanField, HiddenField

from eNMS.database import (
    CustomMediumBlobPickle,
    LARGE_STRING_LENGTH,
    SMALL_STRING_LENGTH,
)
from eNMS.forms.automation import ServiceForm
from eNMS.forms.fields import SubstitutionField
from eNMS.forms.services import NetmikoForm, ValidationForm
from eNMS.models.automation import Run, Service
from eNMS.models.inventory import Device


class NetmikoValidationService(Service):

    __tablename__ = "NetmikoValidationService"

    id = Column(Integer, ForeignKey("Service.id"), primary_key=True)
    has_targets = True
    privileged_mode = Column(Boolean, default=False)
    command = Column(LargeString, default="")
    conversion_method = Column(SmallString, default="text")
    validation_method = Column(SmallString, default="text")
    content_match = Column(LargeString, default="")
    content_match_regex = Column(Boolean, default=False)
    dict_match = Column(MutableDict.as_mutable(CustomMediumBlobPickle), default={})
    negative_logic = Column(Boolean, default=False)
    delete_spaces_before_matching = Column(Boolean, default=False)
    driver = Column(SmallString, default="")
    use_device_driver = Column(Boolean, default=True)
    fast_cli = Column(Boolean, default=False)
    timeout = Column(Integer, default=10.0)
    delay_factor = Column(Float, default=1.0)
    global_delay_factor = Column(Float, default=1.0)
    expect_string = Column(SmallString, default="")
    auto_find_prompt = Column(Boolean, default=True)
    strip_prompt = Column(Boolean, default=True)
    strip_command = Column(Boolean, default=True)

    __mapper_args__ = {"polymorphic_identity": "NetmikoValidationService"}

    def job(self, run: "Run", payload: dict, device: Device) -> dict:
        netmiko_connection = run.netmiko_connection(device)
        command = run.sub(run.command, locals())
        run.log("info", f"Sending '{command}' on {device.name} (Netmiko)")
        expect_string = run.sub(run.expect_string, locals())
        result = run.convert_result(
            netmiko_connection.send_command(
                command,
                delay_factor=run.delay_factor,
                expect_string=run.expect_string or None,
                auto_find_prompt=run.auto_find_prompt,
                strip_prompt=run.strip_prompt,
                strip_command=run.strip_command,
            )
        )
        match = (
            run.sub(run.content_match, locals())
            if run.validation_method == "text"
            else run.sub(run.dict_match, locals())
        )
        return {
            "command": command,
            "match": match,
            "negative_logic": run.negative_logic,
            "result": result,
            "success": run.match_content(result, match),
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
