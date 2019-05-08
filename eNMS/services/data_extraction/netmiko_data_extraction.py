from re import findall
from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, String, Text
from wtforms import (
    BooleanField,
    FloatField,
    HiddenField,
    IntegerField,
    SelectField,
    StringField,
)

from eNMS.controller import controller
from eNMS.database.functions import LARGE_STRING_LENGTH, SMALL_STRING_LENGTH
from eNMS.forms.automation import ServiceForm
from eNMS.models.automation import Service
from eNMS.models.inventory import Device


class NetmikoDataExtractionService(Service):

    __tablename__ = "NetmikoDataExtractionService"

    id = Column(Integer, ForeignKey("Service.id"), primary_key=True)
    has_targets = True
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

    def job(self, payload: dict, device: Device) -> dict:
        netmiko_handler = self.netmiko_connection(device)
        result, success = {}, True
        for i in range(1, 4):
            variable = getattr(self, f"variable{i}")
            regular_expression = getattr(self, f"regular_expression{i}")
            if not variable:
                continue
            command = self.sub(getattr(self, f"command{i}"), locals())
            self.logs.append(f"Sending '{command}' on {device.name} (Netmiko)")
            output = netmiko_handler.send_command(
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
        netmiko_handler.disconnect()
        return {"result": result, "success": True}


class NetmikoDataExtractionForm(ServiceForm):
    form_type = HiddenField(default="NetmikoDataExtractionService")
    variable1 = StringField()
    command1 = StringField()
    regular_expression1 = StringField()
    variable2 = StringField()
    command2 = StringField()
    regular_expression2 = StringField()
    variable3 = StringField()
    command3 = StringField()
    regular_expression3 = StringField()
    driver = SelectField(choices=controller.NETMIKO_DRIVERS)
    use_device_driver = BooleanField(default=True)
    fast_cli = BooleanField()
    timeout = IntegerField()
    delay_factor = FloatField()
    global_delay_factor = FloatField()
