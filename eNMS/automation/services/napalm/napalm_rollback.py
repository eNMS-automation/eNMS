from sqlalchemy import Column, ForeignKey, Integer, PickleType, String
from sqlalchemy.ext.mutable import MutableDict

from eNMS.automation.helpers import napalm_connection, NAPALM_DRIVERS
from eNMS.automation.models import Service, service_classes


class NapalmRollbackService(Service):

    __tablename__ = 'NapalmRollbackService'

    id = Column(Integer, ForeignKey('Service.id'), primary_key=True)
    multiprocessing = True
    driver = Column(String)
    driver_values = NAPALM_DRIVERS
    operating_system = Column(String)
    optional_args = Column(MutableDict.as_mutable(PickleType), default={})
    vendor = Column(String)

    __mapper_args__ = {
        'polymorphic_identity': 'napalm_rollback_service',
    }

    def job(self, device, payload):
        napalm_driver = napalm_connection(self, device)
        napalm_driver.open()
        napalm_driver.rollback()
        napalm_driver.close()
        return {'success': True, 'result': 'Rollback successful'}


service_classes['napalm_rollback_service'] = NapalmRollbackService
