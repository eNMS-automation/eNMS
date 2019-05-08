from sqlalchemy import Boolean, Column, ForeignKey, Integer, PickleType, String
from sqlalchemy.ext.mutable import MutableDict
from wtforms import BooleanField, HiddenField, IntegerField, SelectField, StringField

from eNMS.controller import controller
from eNMS.database.functions import SMALL_STRING_LENGTH
from eNMS.forms.automation import ServiceForm
from eNMS.forms.fields import DictField
from eNMS.models.automation import Service
from eNMS.models.inventory import Device


class NapalmPingService(Service):

    __tablename__ = "NapalmPingService"

    id = Column(Integer, ForeignKey("Service.id"), primary_key=True)
    has_targets = True
    count = Column(Integer, default=0)
    driver = Column(String(SMALL_STRING_LENGTH), default="")
    use_device_driver = Column(Boolean, default=True)
    optional_args = Column(MutableDict.as_mutable(PickleType), default={})
    size = Column(Integer, default=0)
    destination_ip = Column(String(SMALL_STRING_LENGTH), default="")
    source_ip = Column(String(SMALL_STRING_LENGTH), default="")
    timeout = Column(Integer, default=0)
    ttl = Column(Integer, default=0)
    vrf = Column(String(SMALL_STRING_LENGTH), default="")

    __mapper_args__ = {"polymorphic_identity": "NapalmPingService"}

    def job(self, payload: dict, device: Device) -> dict:
        napalm_driver = self.napalm_connection(device)
        napalm_driver.open()
        destination = self.sub(self.destination_ip, locals())
        source = self.sub(self.source_ip, locals())
        self.logs.append(
            f"Running napalm ping from {source}"
            f"to {destination} on {device.ip_address}"
        )
        ping = napalm_driver.ping(
            destination=destination,
            source=source,
            vrf=self.vrf,
            ttl=self.ttl or 255,
            timeout=self.timeout or 2,
            size=self.size or 100,
            count=self.count or 5,
        )
        napalm_driver.close()
        return {"success": "success" in ping, "result": ping}


class NapalmPingForm(ServiceForm):
    form_type = HiddenField(default="NapalmPingService")
    count = IntegerField()
    driver = SelectField(choices=controller.NAPALM_DRIVERS)
    use_device_driver = BooleanField()
    optional_args = DictField()
    size = IntegerField()
    destination_ip = StringField()
    source_ip = StringField()
    timeout = IntegerField()
    ttl = IntegerField()
    vrf = StringField()
