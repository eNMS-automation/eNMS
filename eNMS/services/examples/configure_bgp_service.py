from sqlalchemy import ForeignKey, Integer
from wtforms import HiddenField, IntegerField, StringField

from eNMS.database.dialect import Column, SmallString
from eNMS.forms.automation import ServiceForm
from eNMS.models.automation import Service
from eNMS.models.execution import Run
from eNMS.models.inventory import Device


class ConfigureBgpService(Service):

    __tablename__ = "configure_bgp_service"

    id = Column(Integer, ForeignKey("service.id"), primary_key=True)
    has_targets = True
    local_as = Column(Integer, default=0)
    loopback = Column(SmallString)
    loopback_ip = Column(SmallString)
    neighbor_ip = Column(SmallString)
    remote_as = Column(Integer, default=0)
    vrf_name = Column(SmallString)
    driver = "ios"

    __mapper_args__ = {"polymorphic_identity": "configure_bgp_service"}

    def job(self, run: "Run", payload, device: Device):
        napalm_connection = run.napalm_connection(device)
        config = f"""
            ip vrf {run.vrf_name}
            rd {run.local_as}:235
            route-target import {run.local_as}:410
            route-target export {run.local_as}:400
            maximum route 10000 80
            interface {run.loopback}
            ip vrf forwarding {run.vrf_name}
            ip address {run.loopback_ip} 255.255.255.255
            router bgp {run.local_as}
            address-family ipv4 vrf {run.vrf_name}
            network {run.loopback_ip} mask 255.255.255.255
            neighbor {run.neighbor_ip} remote-as {run.remote_as}
            neighbor {run.neighbor_ip} activate
            neighbor {run.neighbor_ip} send-community both
            neighbor {run.neighbor_ip} as-override
            exit-address-family
        """
        config = "\n".join(config.splitlines())
        run.log("info", f"Pushing BGP configuration on {device.name} (Napalm)")
        getattr(napalm_connection, "load_merge_candidate")(config=config)
        napalm_connection.commit_config()
        return {"success": True, "result": f"Config push ({config})"}


class ConfigureBgpForm(ServiceForm):
    form_type = HiddenField(default="configure_bgp_service")
    local_as = IntegerField("Local AS", default=0)
    loopback = StringField("Loopback", default="Lo42")
    loopback_ip = StringField("Loopback IP")
    neighbor_ip = StringField("Neighbor IP")
    remote_as = IntegerField("Remote AS")
    vrf_name = StringField("VRF Name")
