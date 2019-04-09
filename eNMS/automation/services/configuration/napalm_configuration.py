from sqlalchemy import Boolean, Column, ForeignKey, Integer, PickleType, String
from sqlalchemy.ext.mutable import MutableDict

from eNMS.automation.functions import NAPALM_DRIVERS
from eNMS.automation.models import Service
from eNMS.classes import service_classes
from eNMS.inventory.models import Device


class NapalmConfigurationService(Service):

    __tablename__ = "NapalmConfigurationService"

    id = Column(Integer, ForeignKey("Service.id"), primary_key=True)
    has_targets = True
    action = Column(String(255))
    action_values = (
        ("load_merge_candidate", "Load merge"),
        ("load_replace_candidate", "Load replace"),
    )
    content = Column(String(255))
    content_textarea = True
    driver = Column(String(255))
    driver_values = NAPALM_DRIVERS
    use_device_driver = Column(Boolean, default=True)
    optional_args = Column(MutableDict.as_mutable(PickleType), default={})

    __mapper_args__ = {"polymorphic_identity": "NapalmConfigurationService"}

    def job(self, payload: dict, device: Device) -> dict:
        napalm_driver = self.napalm_connection(device)
        napalm_driver.open()
        self.logs.append(f"Pushing configuration on {device.name} (Napalm)")
        config = "\n".join(self.sub(self.content, locals()).splitlines())
        getattr(napalm_driver, self.action)(config=config)
        napalm_driver.commit_config()
        napalm_driver.close()
        return {"success": True, "result": f"Config push ({config})"}


service_classes["NapalmConfigurationService"] = NapalmConfigurationService
