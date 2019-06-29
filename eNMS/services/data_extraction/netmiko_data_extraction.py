from re import findall
from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, String, Text
from typing import Optional
from wtforms import HiddenField, StringField

from eNMS.database import LARGE_STRING_LENGTH, SMALL_STRING_LENGTH
from eNMS.forms.automation import ServiceForm
from eNMS.forms.fields import SubstitutionField
from eNMS.forms.services import NetmikoForm
from eNMS.models.automation import Job, Service
from eNMS.models.inventory import Device


class NetmikoDataExtractionService(Service):

    __tablename__ = "NetmikoDataExtractionService"

    id = Column(Integer, ForeignKey("Service.id"), primary_key=True)
    has_targets = True
    privileged_mode = Column(Boolean, default=False)
    variable1 = Column(String(SMALL_STRING_LENGTH), default="")
    command1 = Column(String(SMALL_STRING_LENGTH), default="")
    regular_expression1 = Column(Text(LARGE_STRING_LENGTH), default="")
    variable2 = Column(String(SMALL_STRING_LENGTH), default="")
    command2 = Column(String(SMALL_STRING_LENGTH), default="")
    regular_expression2 = Column(Text(LARGE_STRING_LENGTH), default="")
    variable3 = Column(String(SMALL_STRING_LENGTH), default="")
    command3 = Column(String(SMALL_STRING_LENGTH), default="")
    regular_expression3 = Column(Text(LARGE_STRING_LENGTH), default="")
    driver = Column(String(SMALL_STRING_LENGTH), default="")
    use_device_driver = Column(Boolean, default=True)
    fast_cli = Column(Boolean, default=False)
    timeout = Column(Integer, default=10.0)
    delay_factor = Column(Float, default=1.0)
    global_delay_factor = Column(Float, default=1.0)

    __mapper_args__ = {"polymorphic_identity": "NetmikoDataExtractionService"}

    def job(
        self,
        payload: dict,
        device: Optional[Device] = None,
        parent: Optional[Job] = None,
    ) -> dict:
        netmiko_connection = self.netmiko_connection(device, parent)
        result, success = {}, True
        for i in range(1, 4):
            variable = getattr(self, f"variable{i}")
            regular_expression = getattr(self, f"regular_expression{i}")
            if not variable:
                continue
            command = self.sub(getattr(self, f"command{i}"), locals())
            self.logs.append(f"Sending '{command}' on {device.name} (Netmiko)")
            output = netmiko_connection.send_command(
                command, delay_factor=self.delay_factor
            )
            match = findall(regular_expression, output)
            if not match:
                success = False
            result[variable] = {
                "command": command,
                "regular_expression": regular_expression,
                "output": output,
                "value": match,
            }
        return {"result": result, "success": True}


class NetmikoDataExtractionForm(ServiceForm, NetmikoForm):
    form_type = HiddenField(default="NetmikoDataExtractionService")
    variable1 = StringField()
    command1 = SubstitutionField()
    regular_expression1 = StringField()
    variable2 = StringField()
    command2 = SubstitutionField()
    regular_expression2 = StringField()
    variable3 = StringField()
    command3 = SubstitutionField()
    regular_expression3 = StringField()
    groups = {
        "Main Parameters": [
            "variable1",
            "command1",
            "regular_expression1",
            "variable2",
            "command2",
            "regular_expression2",
            "variable3",
            "command3",
            "regular_expression3",
        ],
        "Netmiko Parameters": NetmikoForm.group,
    }
