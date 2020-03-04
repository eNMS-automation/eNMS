from sqlalchemy import Boolean, ForeignKey, Integer

from eNMS.database.dialect import Column, MutableDict, SmallString
from eNMS.forms.fields import HiddenField, IntegerField, StringField
from eNMS.forms.automation import NapalmForm
from eNMS.models.automation import ConnectionService


class NapalmPingService(ConnectionService):

    __tablename__ = "napalm_ping_service"
    pretty_name = "NAPALM Ping"
    parent_type = "connection_service"
    id = Column(Integer, ForeignKey("connection_service.id"), primary_key=True)
    count = Column(Integer, default=0)
    driver = Column(SmallString)
    use_device_driver = Column(Boolean, default=True)
    timeout = Column(Integer, default=60)
    optional_args = Column(MutableDict)
    packet_size = Column(Integer, default=0)
    destination_ip = Column(SmallString)
    source_ip = Column(SmallString)
    timeout = Column(Integer, default=0)
    ttl = Column(Integer, default=0)
    vrf = Column(SmallString)

    __mapper_args__ = {"polymorphic_identity": "napalm_ping_service"}

    def job(self, run, payload, device):
        napalm_connection = run.napalm_connection(device)
        destination = run.sub(run.destination_ip, locals())
        source = run.sub(run.source_ip, locals())
        run.log("info", f"NAPALM PING : {source} -> {destination}", device)
        ping = napalm_connection.ping(
            destination=destination,
            source=source,
            vrf=run.vrf,
            ttl=run.ttl or 255,
            timeout=run.timeout or 2,
            size=run.packet_size or 100,
            count=run.count or 5,
        )
        return {"success": "success" in ping, "result": ping}


class NapalmPingForm(NapalmForm):
    form_type = HiddenField(default="napalm_ping_service")
    count = IntegerField(default=5)
    packet_size = IntegerField(default=100)
    destination_ip = StringField(substitution=True)
    source_ip = StringField(substitution=True)
    timeout = IntegerField(default=2)
    ttl = IntegerField(default=255)
    vrf = StringField()
    groups = {
        "Ping Parameters": {
            "commands": [
                "count",
                "packet_size",
                "destination_ip",
                "source_ip",
                "timeout",
                "ttl",
                "vrf",
            ],
            "default": "expanded",
        },
        **NapalmForm.groups,
    }
