from sqlalchemy import Boolean, Column, ForeignKey, Integer, PickleType, String
from sqlalchemy.ext.mutable import MutableDict
from typing import Optional
from wtforms import HiddenField, IntegerField, StringField

from eNMS.database import SMALL_STRING_LENGTH
from eNMS.forms.automation import ServiceForm
from eNMS.forms.fields import SubstitutionField
from eNMS.forms.services import NapalmForm
from eNMS.models.automation import Job, Service
from eNMS.models.inventory import Device


class NapalmTracerouteService(Service):

    __tablename__ = "NapalmTracerouteService"

    id = Column(Integer, ForeignKey("Service.id"), primary_key=True)
    has_targets = True
    driver = Column(String(SMALL_STRING_LENGTH), default="")
    use_device_driver = Column(Boolean, default=True)
    optional_args = Column(MutableDict.as_mutable(PickleType), default={})
    destination_ip = Column(String(SMALL_STRING_LENGTH), default="")
    source_ip = Column(String(SMALL_STRING_LENGTH), default="")
    timeout = Column(Integer, default=0)
    ttl = Column(Integer, default=0)
    vrf = Column(String(SMALL_STRING_LENGTH), default="")

    __mapper_args__ = {"polymorphic_identity": "NapalmTracerouteService"}

    def job(
        self,
        payload: dict,
        timestamp: str,
        device: Device,
        parent: Optional[Job] = None,
    ) -> dict:
        napalm_connection = self.napalm_connection(device, parent)
        destination = self.sub(self.destination_ip, locals())
        source = self.sub(self.source_ip, locals())
        self.log(
            parent,
            "info",
            f"Running napalm traceroute from {source}"
            f"to {destination} on {device.ip_address}",
        )
        traceroute = napalm_connection.traceroute(
            destination=destination,
            source=self.source,
            vrf=self.vrf,
            ttl=self.ttl or 255,
            timeout=self.timeout or 2,
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
