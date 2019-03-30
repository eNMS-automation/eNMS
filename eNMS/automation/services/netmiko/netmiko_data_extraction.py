from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, PickleType, String
from sqlalchemy.ext.mutable import MutableDict

from eNMS.automation.functions import NETMIKO_DRIVERS
from eNMS.automation.models import Service
from eNMS.base.classes import service_classes
from eNMS.inventory.models import Device


class NetmikoDataExtractionService(Service):

    __tablename__ = "NetmikoDataExtractionService"

    id = Column(Integer, ForeignKey("Service.id"), primary_key=True)
    has_targets = True
    command = Column(String)
    variable_name = Column(String)
    regular_expression = Column(String)
    find_all_matches = Column(Boolean, default=False)
    driver = Column(String)
    driver_values = NETMIKO_DRIVERS
    use_device_driver = Column(Boolean, default=True)
    fast_cli = Column(Boolean, default=False)
    timeout = Column(Integer, default=10.0)
    delay_factor = Column(Float, default=1.0)
    global_delay_factor = Column(Float, default=1.0)

    __mapper_args__ = {"polymorphic_identity": "NetmikoDataExtractionService"}

    def job(self, payload: dict, device: Device) -> dict:
        netmiko_handler = self.netmiko_connection(device)
        command = self.sub(self.command, locals())
        result = netmiko_handler.send_command(command, delay_factor=self.delay_factor)
        netmiko_handler.disconnect()
        return {
            "negative_logic": self.negative_logic,
            "result": result,
            "success": True,
        }


service_classes["NetmikoDataExtractionService"] = NetmikoDataExtractionService
