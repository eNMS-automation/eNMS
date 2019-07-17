from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, String, Text
from typing import Optional
from wtforms import HiddenField
from wtforms.widgets import TextArea

from eNMS.database import LARGE_STRING_LENGTH, SMALL_STRING_LENGTH
from eNMS.forms.automation import ServiceForm
from eNMS.forms.fields import SubstitutionField
from eNMS.forms.services import NetmikoForm
from eNMS.models.automation import Job, Service
from eNMS.models.inventory import Device


class MultilineNetmikoValidationService(Service):

    __tablename__ = "MultilineNetmikoValidationService"

    id = Column(Integer, ForeignKey("Service.id"), primary_key=True)
    has_targets = True
    privileged_mode = Column(Boolean, default=False)
    commands = Column(Text(LARGE_STRING_LENGTH), default="")
    matches = Column(Text(LARGE_STRING_LENGTH), default="")
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

    __mapper_args__ = {"polymorphic_identity": "MultilineNetmikoValidationService"}

    def job(self, payload: dict, device: Device, parent: Optional[Job] = None) -> dict:
        netmiko_connection = self.netmiko_connection(device, parent)
        commands = self.commands.strip().splitlines()
        matches = self.matches.strip().splitlines()
        results = {"success": True}
        for command, match in zip(commands, matches):
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
            success = match in result
            results[command] = {"match": match, "result": result, "success": success}
            if not success:
                results["success"] = False
                break
        return results


class MultilineNetmikoValidationForm(ServiceForm, NetmikoForm):
    form_type = HiddenField(default="MultilineNetmikoValidationService")
    commands = SubstitutionField(
        widget=TextArea(),
        render_kw={"rows": 10},
        default="""
command1
command2
command3
etc...""",
    )
    matches = SubstitutionField(
        widget=TextArea(),
        render_kw={"rows": 10},
        default="""
expected string for command1
expected string for command2
expected string for command3
If you're not expecting anything (you don't need to validate the result),
leave an EMPTY LINE to keep the order intact.
etc...""",
    )
    expect_string = SubstitutionField()
    auto_find_prompt = BooleanField(default=True)
    strip_prompt = BooleanField(default=True)
    strip_command = BooleanField(default=True)
    groups = {
        "Main Parameters": [
            "commands",
            "matches",
            "expect_string",
            "auto_find_prompt",
            "strip_prompt",
            "strip_command",
        ],
        "Netmiko Parameters": NetmikoForm.group,
    }
