from sqlalchemy import Boolean, ForeignKey, Integer
from wtforms import HiddenField, IntegerField, StringField

from eNMS.database.dialect import Column, MutableDict, SmallString
from eNMS.forms.fields import StringField
from eNMS.forms.automation import NapalmForm
from eNMS.models.automation import ConnectionService


class NapalmTracerouteService(ConnectionService):

    __tablename__ = "napalm_traceroute_service"
    pretty_name = "NAPALM Traceroute"
    parent_type = "connection_service"
    id = Column(Integer, ForeignKey("connection_service.id"), primary_key=True)
    driver = Column(SmallString)
    use_device_driver = Column(Boolean, default=True)
    timeout = Column(Integer, default=60)
    optional_args = Column(MutableDict)
    destination_ip = Column(SmallString)
    source_ip = Column(SmallString)
    timeout = Column(Integer, default=0)
    ttl = Column(Integer, default=0)
    vrf = Column(SmallString)

    __mapper_args__ = {"polymorphic_identity": "napalm_traceroute_service"}

    def job(self, run, payload, device):
        napalm_connection = run.napalm_connection(device)
        destination = run.sub(run.destination_ip, locals())
        source = run.sub(run.source_ip, locals())
        run.log("info", f"NAPALM TRACEROUTE : {source} -> {destination}", device)
        traceroute = napalm_connection.traceroute(
            destination=destination,
            source=run.source,
            vrf=run.vrf,
            ttl=run.ttl or 255,
            timeout=run.timeout or 2,
        )
        return {"success": "success" in traceroute, "result": traceroute}


class NapalmTracerouteForm(NapalmForm):
    form_type = HiddenField(default="napalm_traceroute_service")
    destination_ip = StringField(substitution=True)
    source_ip = StringField(substitution=True)
    timeout = IntegerField(default=2)
    ttl = IntegerField(default=255)
    vrf = StringField()
    groups = {
        "Ping Parameters": {
            "commands": ["destination_ip", "source_ip", "timeout", "ttl", "vrf"],
            "default": "expanded",
        },
        **NapalmForm.groups,
    }
