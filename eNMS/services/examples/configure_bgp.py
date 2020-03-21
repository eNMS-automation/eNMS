from sqlalchemy import ForeignKey, Integer

from eNMS.database import db
from eNMS.forms.automation import NapalmForm
from eNMS.forms.fields import HiddenField, IntegerField, StringField

from eNMS.models.automation import ConnectionService


class ConfigureBgpService(ConnectionService):

    __tablename__ = "configure_bgp_service"
    pretty_name = "Configure BGP"
    parent_type = "connection_service"
    id = db.Column(Integer, ForeignKey("connection_service.id"), primary_key=True)
    local_as = db.Column(Integer, default=0)
    loopback = db.Column(db.SmallString)
    loopback_ip = db.Column(db.SmallString)
    neighbor_ip = db.Column(db.SmallString)
    remote_as = db.Column(Integer, default=0)
    vrf_name = db.Column(db.SmallString)
    optional_args = db.Column(db.Dict)
    driver = "ios"
    use_device_driver = True
    timeout = 1

    __mapper_args__ = {"polymorphic_identity": "configure_bgp_service"}

    def job(self, run, payload, device):
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
        run.log("info", "Pushing BGP configuration with Napalm", device)
        napalm_connection.load_merge_candidate(config=config)
        napalm_connection.commit_config()
        return {"success": True, "result": f"Config push ({config})"}


class ConfigureBgpForm(NapalmForm):
    form_type = HiddenField(default="configure_bgp_service")
    local_as = IntegerField("Local AS", default=0)
    loopback = StringField("Loopback", default="Lo42")
    loopback_ip = StringField("Loopback IP")
    neighbor_ip = StringField("Neighbor IP")
    remote_as = IntegerField("Remote AS")
    vrf_name = StringField("VRF Name")
    groups = {
        "Main Parameters": {
            "commands": [
                "local_as",
                "loopback",
                "loopback_ip",
                "neighbor_ip",
                "remote_as",
                "vrf_name",
            ],
            "default": "expanded",
        },
        **NapalmForm.groups,
    }
