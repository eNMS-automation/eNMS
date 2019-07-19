from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, String, Text
from sqlalchemy.ext.mutable import MutableDict
from typing import Optional
from wtforms import HiddenField

from eNMS.database import (
    CustomMediumBlobPickle,
    SMALL_STRING_LENGTH,
    LARGE_STRING_LENGTH,
)
from eNMS.forms.automation import ServiceForm
from eNMS.forms.fields import SubstitutionField
from eNMS.forms.services import NetmikoForm, ValidationForm
from eNMS.models.automation import Job, Service
from eNMS.models.inventory import Device


class NetmikoPromptsService(Service):

    __tablename__ = "NetmikoPromptsService"

    id = Column(Integer, ForeignKey("Service.id"), primary_key=True)
    has_targets = True
    privileged_mode = Column(Boolean, default=False)
    command = Column(String(SMALL_STRING_LENGTH), default="")
    confirmation1 = Column(Text(LARGE_STRING_LENGTH), default="")
    response1 = Column(String(SMALL_STRING_LENGTH), default="")
    confirmation2 = Column(Text(LARGE_STRING_LENGTH), default="")
    response2 = Column(String(SMALL_STRING_LENGTH), default="")
    confirmation3 = Column(Text(LARGE_STRING_LENGTH), default="")
    response3 = Column(String(SMALL_STRING_LENGTH), default="")
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

    __mapper_args__ = {"polymorphic_identity": "NetmikoPromptsService"}

    def job(self, payload: dict, device: Device, parent: Optional[Job] = None) -> dict:
        netmiko_connection = self.netmiko_connection(device, parent)
        command = self.sub(self.command, locals())
        results = {}
        self.logs.append(f"Sending '{command}' on {device.name} (Netmiko)")
        result = netmiko_connection.send_command_timing(
            command, delay_factor=self.delay_factor
        )
        response1 = self.sub(self.response1, locals())
        confirmation1 = self.sub(self.confirmation1, locals())
        results[command] = {"result": result, "match": confirmation1}
        if confirmation1 not in result:
            results.update({"success": False, "result": result, "match": confirmation1})
            return results
        elif response1:
            result = netmiko_connection.send_command_timing(
                response1, delay_factor=self.delay_factor
            )
            confirmation2 = self.sub(self.confirmation2, locals())
            results[response1] = {"result": result, "match": confirmation2}
            response2 = self.sub(self.response2, locals())
            if confirmation2 not in result:
                results.update(
                    {"success": False, "result": result, "match": confirmation2}
                )
                return results
            elif response2:
                result = netmiko_connection.send_command_timing(
                    response2, delay_factor=self.delay_factor
                )
                confirmation3 = self.sub(self.confirmation3, locals())
                results[response2] = {"result": result, "match": confirmation3}
                response3 = self.sub(self.response3, locals())
                if confirmation3 not in result:
                    results.update(
                        {"success": False, "result": result, "match": confirmation3}
                    )
                    return results
                elif response3:
                    result = netmiko_connection.send_command_timing(
                        response3, delay_factor=self.delay_factor
                    )
        match = self.sub(self.content_match, locals())
        return {
            "expected": match if self.validation_method == "text" else self.dict_match,
            "negative_logic": self.negative_logic,
            "result": result,
            "success": self.match_content(result, match),
        }


class NetmikoPromptsForm(ServiceForm, NetmikoForm, ValidationForm):
    form_type = HiddenField(default="NetmikoPromptsService")
    command = SubstitutionField()
    confirmation1 = SubstitutionField()
    response1 = SubstitutionField()
    confirmation2 = SubstitutionField()
    response2 = SubstitutionField()
    confirmation3 = SubstitutionField()
    response3 = SubstitutionField()
    groups = {
        "Main Parameters": [
            "command",
            "confirmation1",
            "response1",
            "confirmation2",
            "response2",
            "confirmation3",
            "response3",
        ],
        "Netmiko Parameters": NetmikoForm.group,
        "String Validation Parameters": ValidationForm.group,
    }
