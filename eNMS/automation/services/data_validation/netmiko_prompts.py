from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, PickleType, String
from sqlalchemy.ext.mutable import MutableDict

from eNMS.automation.functions import NETMIKO_DRIVERS
from eNMS.automation.models import Service
from eNMS.classes import service_classes
from eNMS.inventory.models import Device


class NetmikoPromptsService(Service):

    __tablename__ = "NetmikoPromptsService"

    id = Column(Integer, ForeignKey("Service.id"), primary_key=True)
    has_targets = True
    command = Column(String(255))
    confirmation1 = Column(String(255))
    response1 = Column(String(255))
    confirmation2 = Column(String(255))
    response2 = Column(String(255))
    confirmation3 = Column(String(255))
    response3 = Column(String(255))
    conversion_method = Column(String(255), default="text")
    conversion_method_values = (
        ("text", "Text"),
        ("json", "Json dictionary"),
        ("xml", "XML dictionary"),
    )
    validation_method = Column(String(255), default="text")
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
    driver = Column(String(255))
    driver_values = NETMIKO_DRIVERS
    use_device_driver = Column(Boolean, default=True)
    fast_cli = Column(Boolean, default=False)
    timeout = Column(Integer, default=10.0)
    delay_factor = Column(Float, default=1.0)
    global_delay_factor = Column(Float, default=1.0)

    __mapper_args__ = {"polymorphic_identity": "NetmikoPromptsService"}

    def job(self, payload: dict, device: Device) -> dict:
        netmiko_handler = self.netmiko_connection(device)
        command = self.sub(self.command, locals())
        self.logs.append(f"Sending '{command}' on {device.name} (Netmiko)")
        result = netmiko_handler.send_command_timing(
            command, delay_factor=self.delay_factor
        )
        if self.response1 and self.confirmation1 in result:
            result = netmiko_handler.send_command_timing(
                self.response1, delay_factor=self.delay_factor
            )
            if self.response2 and self.confirmation2 in result:
                result = netmiko_handler.send_command_timing(
                    self.response2, delay_factor=self.delay_factor
                )
                if self.response3 and self.confirmation3 in result:
                    result = netmiko_handler.send_command_timing(
                        self.response3, delay_factor=self.delay_factor
                    )
        match = self.sub(self.content_match, locals())
        netmiko_handler.disconnect()
        return {
            "expected": match if self.validation_method == "text" else self.dict_match,
            "negative_logic": self.negative_logic,
            "result": result,
            "success": self.match_content(result, match),
        }


service_classes["NetmikoPromptsService"] = NetmikoPromptsService
