from sqlalchemy import Column, ForeignKey, Integer

from eNMS.services.connections import napalm_connection
from eNMS.services.models import multiprocessing, Service, service_classes


class NapalmRollbackService(Service):

    __tablename__ = 'NapalmRollbackService'

    id = Column(Integer, ForeignKey('Service.id'), primary_key=True)
    device_multiprocessing = True

    __mapper_args__ = {
        'polymorphic_identity': 'napalm_rollback_service',
    }

    @multiprocessing
    def job(self, task, device, results, incoming_payload):
        try:
            napalm_driver = napalm_connection(device)
            napalm_driver.open()
            napalm_driver.rollback()
            napalm_driver.close()
            result, success = 'Rollback successful', True
        except Exception as e:
            result = f'Napalm rollback did not work because of {e}'
            success = False
        return success, result, incoming_payload


service_classes['Napalm Rollback Service'] = NapalmRollbackService
