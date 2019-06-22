from re import findall
from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, String, Text
from typing import Optional
from wtforms import (
    BooleanField,
    FloatField,
    HiddenField,
    IntegerField,
    SelectField,
    StringField,
)

from eNMS.controller import controller
from eNMS.database import LARGE_STRING_LENGTH, SMALL_STRING_LENGTH
from eNMS.forms.automation import ServiceForm
from eNMS.models.automation import Job, Service
from eNMS.models.inventory import Device


class PayloadRegexExtractionService(Service):

    __tablename__ = "PayloadRegexExtractionService"

    id = Column(Integer, ForeignKey("Service.id"), primary_key=True)
    has_targets = True
    variable1 = Column(String(SMALL_STRING_LENGTH), default="")
    regular_expression1 = Column(Text(LARGE_STRING_LENGTH), default="")
    variable2 = Column(String(SMALL_STRING_LENGTH), default="")
    regular_expression2 = Column(Text(LARGE_STRING_LENGTH), default="")
    variable3 = Column(String(SMALL_STRING_LENGTH), default="")
    regular_expression3 = Column(Text(LARGE_STRING_LENGTH), default="")

    __mapper_args__ = {"polymorphic_identity": "PayloadRegexExtractionService"}

    def job(self, payload: dict, device: Device, parent: Optional[Job] = None) -> dict:
        result, success = {}, True
        for i in range(1, 4):
            variable = getattr(self, f"variable{i}")
            regular_expression = getattr(self, f"regular_expression{i}")
            if not variable:
                continue
            command = self.sub(getattr(self, f"command{i}"), locals())
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
        if not parent:
            netmiko_handler.disconnect()
        return {"result": result, "success": True}


class PayloadDataExtractionForm(ServiceForm):
    form_type = HiddenField(default="PayloadRegexExtractionService")
    variable1 = StringField()
    regular_expression1 = StringField()
    variable2 = StringField()
    regular_expression2 = StringField()
    variable3 = StringField()
    regular_expression3 = StringField()
