from sqlalchemy import Boolean, Column, ForeignKey, Integer, PickleType, String
from sqlalchemy.ext.mutable import MutableDict
from wtforms import HiddenField, IntegerField, StringField

from eNMS.database.dialect import SmallString
from eNMS.forms.automation import ServiceForm
from eNMS.forms.fields import SubstitutionField
from eNMS.forms.services import NapalmForm
from eNMS.models.automation import Run, Service
from eNMS.models.inventory import Device


class NapalmTracerouteService(Service):

    __tablename__ = "NapalmTracerouteService"

    id = Column(Integer, ForeignKey("Service.id"), primary_key=True)
    has_targets = True
    driver = Column(SmallString, default="")
    use_device_driver = Column(Boolean, default=True)
    optional_args = Column(MutableDict, default={})
    destination_ip = Column(SmallString, default="")
    source_ip = Column(SmallString, default="")
    timeout = Column(Integer, default=0)
    ttl = Column(Integer, default=0)
    vrf = Column(SmallString, default="")

    __mapper_args__ = {"polymorphic_identity": "NapalmTracerouteService"}

    def job(self, run: "Run", payload: dict, device: Device) -> dict:
        napalm_connection = run.napalm_connection(device)
        destination = run.sub(run.destination_ip, locals())
        source = run.sub(run.source_ip, locals())
        run.log(
            "info",
            f"Running napalm traceroute from {source}"
            f"to {destination} on {device.ip_address}",
        )
        traceroute = napalm_connection.traceroute(
            destination=destination,
            source=run.source,
            vrf=run.vrf,
            ttl=run.ttl or 255,
            timeout=run.timeout or 2,
        )
        return {"success": "success" in traceroute, "result": traceroute}


class NapalmTracerouteForm(ServiceForm, NapalmForm):
    form_type = HiddenField(default="NapalmTracerouteService")
    destination_ip = SubstitutionField()
    source_ip = SubstitutionField()
    timeout = IntegerField()
    ttl = IntegerField()
    vrf = StringField()
    groups = {
        "Napalm Parameters": NapalmForm.group,
        "Ping Parameters": ["destination_ip", "source_ip", "timeout", "ttl", "vrf"],
    }
