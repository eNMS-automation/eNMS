from sqlalchemy import Boolean, Column, ForeignKey, Integer, PickleType, String
from sqlalchemy.ext.mutable import MutableDict

from eNMS.controller import controller
from eNMS.models import register_class
from eNMS.models.automation import Service
from eNMS.models.inventory import Device


class NapalmTracerouteService(Service, metaclass=register_class):

    __tablename__ = "NapalmTracerouteService"

    id = Column(Integer, ForeignKey("Service.id"), primary_key=True)
    has_targets = True
    driver = Column(String(255), default="")
    driver_values = controller.NAPALM_DRIVERS
    use_device_driver = Column(Boolean, default=True)
    optional_args = Column(MutableDict.as_mutable(PickleType), default={})
    destination_ip = Column(String(255), default="")
    source_ip = Column(String(255), default="")
    timeout = Column(Integer, default=0)
    ttl = Column(Integer, default=0)
    vrf = Column(String(255), default="")

    __mapper_args__ = {"polymorphic_identity": "NapalmTracerouteService"}

    def job(self, payload: dict, device: Device) -> dict:
        napalm_driver = self.napalm_connection(device)
        napalm_driver.open()
        destination = self.sub(self.destination_ip, locals())
        source = self.sub(self.source_ip, locals())
        self.logs.append(
            f"Running napalm traceroute from {source}"
            f"to {destination} on {device.ip_address}"
        )
        traceroute = napalm_driver.traceroute(
            destination=destination,
            source=self.source,
            vrf=self.vrf,
            ttl=self.ttl or 255,
            timeout=self.timeout or 2,
        )
        napalm_driver.close()
        return {"success": "success" in traceroute, "result": traceroute}
