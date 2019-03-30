from re import findall, match
from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, String

from eNMS.automation.functions import NETMIKO_DRIVERS
from eNMS.automation.models import Service
from eNMS.base.classes import service_classes
from eNMS.inventory.models import Device


class NetmikoDataExtractionService(Service):

    __tablename__ = "NetmikoDataExtractionService"

    id = Column(Integer, ForeignKey("Service.id"), primary_key=True)
    has_targets = True
    command = Column(String)
    variable = Column(String)
    regular_expression = Column(String)
    find_all = Column(Boolean, default=False)
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
        output = netmiko_handler.send_command(command, delay_factor=self.delay_factor)
        variables = {}
        result = (
            findall(self.regular_expression, output)
            if self.find_all
            else match(self.regular_expression, output)
        )
        if not result:
            return {
                "command": command,
                "output": output,
                "regular_expression": self.regular_expression,
                "success": False,
            }
        else:
            value = result if self.find_all else result.group(1)
        netmiko_handler.disconnect()
        return {self.variable: value, "success": True}


service_classes["NetmikoDataExtractionService"] = NetmikoDataExtractionService
