from sqlalchemy import Column, ForeignKey, Integer, String

from eNMS.automation.models import Service
from eNMS.classes import service_classes
from eNMS.inventory.models import Device


class ConfigureBgpService(Service):

    __tablename__ = "ConfigureBgpService"

    id = Column(Integer, ForeignKey("Service.id"), primary_key=True)
    has_targets = True
    local_as = Column(Integer)
    loopback = Column(String(255))
    loopback_ip = Column(String(255))
    neighbor_ip = Column(String(255))
    remote_as = Column(Integer)
    vrf_name = Column(String(255))
    driver = "ios"

    __mapper_args__ = {"polymorphic_identity": "ConfigureBgpService"}

    def job(self, payload: dict, device: Device) -> dict:
        napalm_driver = self.napalm_connection(device)
        napalm_driver.open()
        config = f"""
            ip vrf {self.vrf_name}
            rd {self.local_as}:235
            route-target import {self.local_as}:410
            route-target export {self.local_as}:400
            maximum route 10000 80
            interface {self.loopback}
            ip vrf forwarding {self.vrf_name}
            ip address {self.loopback_ip} 255.255.255.255
            router bgp {self.local_as}
            address-family ipv4 vrf {self.vrf_name}
            network {self.loopback_ip} mask 255.255.255.255
            neighbor {self.neighbor_ip} remote-as {self.remote_as}
            neighbor {self.neighbor_ip} activate
            neighbor {self.neighbor_ip} send-community both
            neighbor {self.neighbor_ip} as-override
            exit-address-family
        """
        config = "\n".join(config.splitlines())
        self.logs.append(f"Pushing BGP configuration on {device.name} (Napalm)")
        getattr(napalm_driver, "load_merge_candidate")(config=config)
        napalm_driver.commit_config()
        napalm_driver.close()
        return {"success": True, "result": f"Config push ({config})"}


service_classes["ConfigureBgpService"] = ConfigureBgpService
