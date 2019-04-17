from sqlalchemy import Boolean, Column, ForeignKey, Integer, PickleType, String
from sqlalchemy.ext.mutable import MutableDict

from eNMS.helpers import NAPALM_DRIVERS
from eNMS.models import Service
from eNMS.classes import service_classes
from eNMS.models import Device


class NapalmTracerouteService(Service):

    __tablename__ = "NapalmTracerouteService"

    id = Column(Integer, ForeignKey("Service.id"), primary_key=True)
    has_targets = True
    driver = Column(String(255))
    driver_values = NAPALM_DRIVERS
    use_device_driver = Column(Boolean, default=True)
    optional_args = Column(MutableDict.as_mutable(PickleType), default={})
    source_ip = Column(String(255))
    timeout = Column(Integer)
    ttl = Column(Integer)
    vrf = Column(String(255))

    __mapper_args__ = {"polymorphic_identity": "NapalmTracerouteService"}

    def job(self, payload: dict, device: Device) -> dict:
        napalm_driver = self.napalm_connection(device)
        napalm_driver.open()
        self.logs.append(
            f"Running traceroute from {self.source} to {device.ip_address}"
        )
        traceroute = napalm_driver.traceroute(
            device.ip_address,
            source=self.source,
            vrf=self.vrf,
            ttl=self.ttl or 255,
            timeout=self.timeout or 2,
        )
        napalm_driver.close()
        return {"success": "success" in traceroute, "result": traceroute}


service_classes["NapalmTracerouteService"] = NapalmTracerouteService
