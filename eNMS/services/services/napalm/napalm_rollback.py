from multiprocessing.pool import ThreadPool
from sqlalchemy import Column, ForeignKey, Integer

from eNMS.services.helpers import napalm_connection
from eNMS.services.models import Service, service_classes


class NapalmRollbackService(Service):

    __tablename__ = 'NapalmRollbackService'

    id = Column(Integer, ForeignKey('Service.id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': 'napalm_rollback_service',
    }

    def job(self, task, incoming_payload):
        targets = task.compute_targets()
        results = {'success': True}
        pool = ThreadPool(processes=len(targets))
        pool.map(self.device_job, [(device, results) for device in targets])
        pool.close()
        pool.join()
        return results

    def device_job(self, args):
        device, results = args
        try:
            napalm_driver = napalm_connection(self, device)
            napalm_driver.open()
            napalm_driver.rollback()
            napalm_driver.close()
            result, success = 'Rollback successful', True
        except Exception as e:
            result, success = f'task failed ({e})', False
            results['success'] = False
        results[device.name] = {'success': success, 'result': result}


service_classes['Napalm Rollback Service'] = NapalmRollbackService
