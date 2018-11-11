from sqlalchemy import Column, ForeignKey, Integer, PickleType, String
from sqlalchemy.ext.mutable import MutableDict

from eNMS.automation.helpers import napalm_connection, NAPALM_DRIVERS
from eNMS.automation.models import Service
from eNMS.base.classes import service_classes


class NapalmTracerouteService(Service):

    __tablename__ = 'NapalmTracerouteService'

    id = Column(Integer, ForeignKey('Service.id'), primary_key=True)
    driver = Column(String)
    driver_values = NAPALM_DRIVERS
    multiprocessing = True
    optional_args = Column(MutableDict.as_mutable(PickleType), default={})
    source_ip = Column(String)
    timeout = Column(Integer)
    ttl = Column(Integer)
    vrf = Column(String)

    __mapper_args__ = {
        'polymorphic_identity': 'NapalmTracerouteService',
    }

    def job(self, device, payload):
        napalm_driver = napalm_connection(self, device)
        napalm_driver.open()
        traceroute = napalm_driver.traceroute(
            device.ip_address,
            source=self.source,
            vrf=self.vrf,
            ttl=self.ttl or 255,
            timeout=self.timeout or 2
        )
        napalm_driver.close()
        return {'success': 'success' in traceroute, 'result': traceroute}


service_classes['NapalmTracerouteService'] = NapalmTracerouteService
