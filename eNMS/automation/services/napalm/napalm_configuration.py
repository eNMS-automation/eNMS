from multiprocessing.pool import ThreadPool
from sqlalchemy import Column, ForeignKey, Integer, PickleType, String
from sqlalchemy.ext.mutable import MutableDict

from eNMS.automation.helpers import napalm_connection, NAPALM_DRIVERS
from eNMS.automation.models import Service, service_classes


class NapalmConfigurationService(Service):

    __tablename__ = 'NapalmConfigurationService'

    id = Column(Integer, ForeignKey('Service.id'), primary_key=True)
    vendor = Column(String)
    operating_system = Column(String)
    action = Column(String)
    action_values = (
        ('load_merge_candidate', 'Load merge'),
        ('load_replace_candidate', 'Load replace')
    )
    content = Column(String)
    driver = Column(String)
    driver_values = NAPALM_DRIVERS
    operating_system = Column(String)
    optional_args = Column(MutableDict.as_mutable(PickleType), default={})
    vendor = Column(String)

    __mapper_args__ = {
        'polymorphic_identity': 'napalm_configuration_service',
    }

    def job(self, task, workflow_results):
        targets = task.compute_targets()
        results = {'success': True, 'devices': {}}
        pool = ThreadPool(processes=len(targets))
        pool.map(self.device_job, [(device, results) for device in targets])
        pool.close()
        pool.join()
        return results

    def device_job(self, args):
        device, results = args
        try:
            napalm_driver = napalm_connection(self, device, self.optional_args)
            napalm_driver.open()
            config = '\n'.join(self.content.splitlines())
            getattr(napalm_driver, self.action)(config=config)
            napalm_driver.commit_config()
            napalm_driver.close()
            result, success = f'Config push ({config})', True
        except Exception as e:
            result, success = f'service failed ({e})', False
            results['success'] = False
        results['devices'][device.name] = {
            'success': success,
            'result': result
        }


service_classes['napalm_configuration_service'] = NapalmConfigurationService
