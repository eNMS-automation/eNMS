from sqlalchemy import Column, ForeignKey, Integer, String

from eNMS.services.helpers import napalm_connection
from eNMS.services.models import Service, service_classes


class NapalmConfigurationService(Service):

    __tablename__ = 'NapalmConfigurationService'

    id = Column(Integer, ForeignKey('Service.id'), primary_key=True)
    vendor = Column(String)
    operating_system = Column(String)
    action = Column(String)
    content = Column(String)
    device_multiprocessing = True

    action_values = (
        ('load_merge_candidate', 'Load merge'),
        ('load_replace_candidate', 'Load replace')
    )

    __mapper_args__ = {
        'polymorphic_identity': 'napalm_configuration_service',
    }

    def job(self, incoming_payload):
        results, global_success = {}, True
        for device in self.task.compute_targets():
            try:
                napalm_driver = napalm_connection(device)
                napalm_driver.open()
                config = '\n'.join(self.content.splitlines())
                getattr(napalm_driver, self.action)(config=config)
                napalm_driver.commit_config()
                napalm_driver.close()
                result, success = f'Config push ({config})', True
            except Exception as e:
                result, success = f'task failed ({e})', False
                global_success = False
            results[device.name] = {'success': success, 'result': result}
        results['success'] = global_success
        return results


service_classes['Napalm Configuration Service'] = NapalmConfigurationService
