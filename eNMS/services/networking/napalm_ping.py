from sqlalchemy import Boolean, Column, ForeignKey, Integer, PickleType, String
from sqlalchemy.ext.mutable import MutableDict

from eNMS.helpers import NAPALM_DRIVERS
from eNMS.models.models import Service
from eNMS.classes import service_classes
from eNMS.models.models import Device


class NapalmPingService(Service):

    __tablename__ = "NapalmPingService"

    id = Column(Integer, ForeignKey("Service.id"), primary_key=True)
    has_targets = True
    count = Column(Integer)
    driver = Column(String(255))
    driver_values = NAPALM_DRIVERS
    use_device_driver = Column(Boolean, default=True)
    optional_args = Column(MutableDict.as_mutable(PickleType), default={})
    size = Column(Integer)
    source_ip = Column(String(255))
    timeout = Column(Integer)
    ttl = Column(Integer)
    vrf = Column(String(255))

    __mapper_args__ = {"polymorphic_identity": "NapalmPingService"}

    def job(self, payload: dict, device: Device) -> dict:
        napalm_driver = self.napalm_connection(device)
        napalm_driver.open()
        self.logs.append(f"Running ping from {self.source_ip} to {device.ip_address}")
        ping = napalm_driver.ping(
            device.ip_address,
            source=self.source_ip,
            vrf=self.vrf,
            ttl=self.ttl or 255,
            timeout=self.timeout or 2,
            size=self.size or 100,
            count=self.count or 5,
        )
        napalm_driver.close()
        return {"success": "success" in ping, "result": ping}


service_classes["NapalmPingService"] = NapalmPingService
