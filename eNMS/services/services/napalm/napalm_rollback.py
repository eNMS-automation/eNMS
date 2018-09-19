from sqlalchemy import Column, Float, ForeignKey, Integer, String

from eNMS.services.custom_service import CustomService, service_classes
from eNMS.services.models import multiprocessing


class NapalmRollbackService(CustomService):

    __tablename__ = 'NapalmRollbackService'

    id = Column(Integer, ForeignKey('CustomService.id'), primary_key=True)
    vendor = Column(String)
    operating_system = Column(String)
    content = Column(String)
    driver = Column(String)
    global_delay_factor = Column(Float, default=1.)
    device_multiprocessing = True

    driver_values = [(driver, driver) for driver in netmiko_drivers]

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
