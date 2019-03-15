from json import load
from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, PickleType, String
from sqlalchemy.ext.mutable import MutableDict
from xmltodict import parse

from eNMS.automation.helpers import NETMIKO_DRIVERS
from eNMS.automation.models import Service
from eNMS.base.classes import service_classes
from eNMS.inventory.models import Device


class NetmikoValidationService(Service):

    __tablename__ = "NetmikoValidationService"

    id = Column(Integer, ForeignKey("Service.id"), primary_key=True)
    has_targets = True
    command = Column(String)
    content_match = Column(String)
    content_match_textarea = True
    content_match_regex = Column(Boolean)
    conversion_method = Column(String, default="text")
    conversion_method_values = (
        ("text", "Text"),
        ("json", "Json dictionary"),
        ("xml", "XML dictionary"),
    )
    dict_match = Column(MutableDict.as_mutable(PickleType), default={})
    negative_logic = Column(Boolean)
    delete_spaces_before_matching = Column(Boolean)
    driver = Column(String)
    driver_values = NETMIKO_DRIVERS
    use_device_driver = Column(Boolean, default=True)
    fast_cli = Column(Boolean, default=False)
    timeout = Column(Integer, default=10.0)
    global_delay_factor = Column(Float, default=1.0)
    validation_method = Column(String, default="text")
    validation_method_values = (
        ("text", "Validation by text match"),
        ("dict_equal", "Validation by dictionnary equality"),
        ("dict_included", "Validation by dictionnary inclusion"),
    )

    __mapper_args__ = {"polymorphic_identity": "NetmikoValidationService"}

    def job(self, payload: dict, device: Device) -> dict:
        netmiko_handler = self.netmiko_connection(device)
        command = self.sub(self.command, locals())
        result = netmiko_handler.send_command(command)
        if self.conversion_method == "json":
            result = load(result)
        elif self.conversion_method == "xml":
            result = parse(result)
        match = self.sub(self.content_match, locals())
        if self.validation_method == "text":
            success = self.match_content(str(result), match)
        else:
            success = self.match_dictionnary(result)
        netmiko_handler.disconnect()
        return {
            "match": match if self.validation_method == "text" else self.dict_match,
            "negative_logic": self.negative_logic,
            "result": result,
            "success": success,
        }


service_classes["NetmikoValidationService"] = NetmikoValidationService
