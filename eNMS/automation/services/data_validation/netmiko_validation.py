from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, PickleType, String
from sqlalchemy.ext.mutable import MutableDict

from eNMS.automation.functions import NETMIKO_DRIVERS
from eNMS.automation.models import Service
from eNMS.classes import service_classes
from eNMS.inventory.models import Device


class NetmikoValidationService(Service):

    __tablename__ = "NetmikoValidationService"

    id = Column(Integer, ForeignKey("Service.id"), primary_key=True)
    has_targets = True
    command = Column(String(255))
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
    negative_logic = Column(Boolean, default=False)
    delete_spaces_before_matching = Column(Boolean)
    driver = Column(String(255))
    driver_values = NETMIKO_DRIVERS
    use_device_driver = Column(Boolean, default=True)
    fast_cli = Column(Boolean, default=False)
    timeout = Column(Integer, default=10.0)
    delay_factor = Column(Float, default=1.0)
    global_delay_factor = Column(Float, default=1.0)

    __mapper_args__ = {"polymorphic_identity": "NetmikoValidationService"}

    def job(self, payload: dict, device: Device) -> dict:
        netmiko_handler = self.netmiko_connection(device)
        command = self.sub(self.command, locals())
        self.logs.append(f"Sending '{command}' on {device.name} (Netmiko)")
        result = netmiko_handler.send_command(command, delay_factor=self.delay_factor)
        match = self.sub(self.content_match, locals())
        netmiko_handler.disconnect()
        return {
            "match": match if self.validation_method == "text" else self.dict_match,
            "negative_logic": self.negative_logic,
            "result": result,
            "success": self.match_content(result, match),
        }


service_classes["NetmikoValidationService"] = NetmikoValidationService
