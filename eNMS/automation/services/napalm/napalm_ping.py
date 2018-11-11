from sqlalchemy import Column, ForeignKey, Integer, PickleType, String
from sqlalchemy.ext.mutable import MutableDict

from eNMS.automation.helpers import napalm_connection, NAPALM_DRIVERS
from eNMS.automation.models import Service
from eNMS.base.classes import service_classes


class NapalmPingService(Service):

    __tablename__ = 'NapalmPingService'

    id = Column(Integer, ForeignKey('Service.id'), primary_key=True)
    multiprocessing = True
    count = Column(Integer)
    driver = Column(String)
    driver_values = NAPALM_DRIVERS
    optional_args = Column(MutableDict.as_mutable(PickleType), default={})
    size = Column(Integer)
    source_ip = Column(String)
    timeout = Column(Integer)
    ttl = Column(Integer)
    vrf = Column(String)

    __mapper_args__ = {
        'polymorphic_identity': 'NapalmPingService',
    }

    def job(self, device, payload):
        napalm_driver = napalm_connection(self, device)
        napalm_driver.open()
        ping = napalm_driver.ping(
            device.ip_address,
            source=self.source,
            vrf=self.vrf,
            ttl=self.ttl or 255,
            timeout=self.timeout or 2,
            size=self.size or 100,
            count=self.count or 5
        )
        napalm_driver.close()
        return {'success': 'success' in ping, 'result': ping}


service_classes['NapalmPingService'] = NapalmPingService
