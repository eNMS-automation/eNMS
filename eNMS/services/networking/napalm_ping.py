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


class NapalmPingService(Service):

    __tablename__ = "NapalmPingService"

    id = Column(Integer, ForeignKey("Service.id"), primary_key=True)
    has_targets = True
    count = Column(Integer, default=0)
    driver = Column(String(SMALL_STRING_LENGTH), default="")
    use_device_driver = Column(Boolean, default=True)
    optional_args = Column(MutableDict.as_mutable(PickleType), default={})
    packet_size = Column(Integer, default=0)
    destination_ip = Column(String(SMALL_STRING_LENGTH), default="")
    source_ip = Column(String(SMALL_STRING_LENGTH), default="")
    timeout = Column(Integer, default=0)
    ttl = Column(Integer, default=0)
    vrf = Column(String(SMALL_STRING_LENGTH), default="")

    __mapper_args__ = {"polymorphic_identity": "NapalmPingService"}

    def job(self, payload: dict, device: Device, parent: Optional[Job] = None) -> dict:
        napalm_connection = self.napalm_connection(device, parent)
        destination = self.sub(self.destination_ip, locals())
        source = self.sub(self.source_ip, locals())
        self.log
            f"Running napalm ping from {source}"
            f"to {destination} on {device.ip_address}"
        )
        ping = napalm_connection.ping(
            destination=destination,
            source=source,
            vrf=self.vrf,
            ttl=self.ttl or 255,
            timeout=self.timeout or 2,
            size=self.packet_size or 100,
            count=self.count or 5,
        )
        return {"success": "success" in ping, "result": ping}


class NapalmPingForm(ServiceForm, NapalmForm):
    form_type = HiddenField(default="NapalmPingService")
    count = IntegerField()
    packet_size = IntegerField()
    destination_ip = SubstitutionField()
    source_ip = SubstitutionField()
    timeout = IntegerField()
    ttl = IntegerField()
    vrf = StringField()
    groups = {
        "Napalm Parameters": NapalmForm.group,
        "Ping Parameters": [
            "count",
            "packet_size",
            "destination_ip",
            "source_ip",
            "timeout",
            "ttl",
            "vrf",
        ],
    }
