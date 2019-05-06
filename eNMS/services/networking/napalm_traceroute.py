from sqlalchemy import Boolean, Column, ForeignKey, Integer, PickleType, String
from sqlalchemy.ext.mutable import MutableDict
from wtforms import BooleanField, HiddenField, IntegerField, SelectField, StringField

from eNMS.controller import controller
from eNMS.database import SMALL_STRING_LENGTH
from eNMS.forms import metaform
from eNMS.forms.automation import ServiceForm
from eNMS.forms.fields import DictField
from eNMS.models import metamodel
from eNMS.models.automation import Service
from eNMS.models.inventory import Device


class NapalmTracerouteService(Service, metaclass=metamodel):

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

    def job(self, payload: dict, device: Device) -> dict:
        napalm_driver = self.napalm_connection(device)
        napalm_driver.open()
        destination = self.sub(self.destination_ip, locals())
        source = self.sub(self.source_ip, locals())
        self.logs.append(
            f"Running napalm traceroute from {source}"
            f"to {destination} on {device.ip_address}"
        )
        traceroute = napalm_driver.traceroute(
            destination=destination,
            source=self.source,
            vrf=self.vrf,
            ttl=self.ttl or 255,
            timeout=self.timeout or 2,
        )
        napalm_driver.close()
        return {"success": "success" in traceroute, "result": traceroute}


class NapalmTracerouteForm(ServiceForm, metaclass=metaform):
    form_type = HiddenField(default="NapalmTracerouteService")
    driver = SelectField(choices=controller.NAPALM_DRIVERS)
    use_device_driver = BooleanField()
    optional_args = DictField()
    destination_ip = StringField()
    source_ip = StringField()
    timeout = IntegerField()
    ttl = IntegerField()
    vrf = StringField()
