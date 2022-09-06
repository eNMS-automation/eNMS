from sqlalchemy import Boolean, ForeignKey, Integer

from eNMS.database import db
from eNMS.fields import HiddenField, IntegerField, StringField
from eNMS.forms import NapalmForm
from eNMS.models.automation import ConnectionService


class NapalmTracerouteService(ConnectionService):

    __tablename__ = "napalm_traceroute_service"
    pretty_name = "NAPALM Traceroute"
    parent_type = "connection_service"
    id = db.Column(Integer, ForeignKey("connection_service.id"), primary_key=True)
    driver = db.Column(db.SmallString)
    timeout = db.Column(Integer, default=60)
    optional_args = db.Column(db.Dict)
    destination_ip = db.Column(db.SmallString)
    source_ip = db.Column(db.SmallString)
    timeout = db.Column(Integer, default=0)
    ttl = db.Column(Integer, default=0)
    vrf = db.Column(db.SmallString)

    __mapper_args__ = {"polymorphic_identity": "napalm_traceroute_service"}

    def job(self, run, device):
        napalm_connection = run.napalm_connection(device)
        destination = run.sub(run.destination_ip, locals())
        source = run.sub(run.source_ip, locals())
        run.log("info", f"NAPALM TRACEROUTE : {source} -> {destination}", device)
        traceroute = napalm_connection.traceroute(
            destination=destination,
            source=source,
            vrf=run.vrf,
            ttl=run.ttl or 255,
            timeout=run.timeout or 2,
        )
        return {"success": "success" in traceroute, "result": traceroute}


class NapalmTracerouteForm(NapalmForm):
    form_type = HiddenField(default="napalm_traceroute_service")
    destination_ip = StringField(substitution=True)
    source_ip = StringField(substitution=True)
    ttl = IntegerField(default=255)
    vrf = StringField(label="vrf or router", substitution=True)
    groups = {
        "Traceroute Parameters": {
            "commands": ["destination_ip", "source_ip", "timeout", "ttl", "vrf"],
            "default": "expanded",
        },
        **NapalmForm.groups,
    }
