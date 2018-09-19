from sqlalchemy import Column, Float, ForeignKey, Integer, String

from eNMS.services.custom_service import CustomService, service_classes
from eNMS.services.models import multiprocessing


class NapalmConfigurationService(CustomService):

    __tablename__ = 'NapalmConfigurationService'

    id = Column(Integer, ForeignKey('CustomService.id'), primary_key=True)
    vendor = Column(String)
    operating_system = Column(String)
    action = Column(String)
    content = Column(String)
    device_multiprocessing = True

    __mapper_args__ = {
        'polymorphic_identity': 'netmiko_configuration_service',
    }

    @multiprocessing
    def job(self, task, device, results, incoming_payload):
        try:
            napalm_driver = napalm_connection(device)
            napalm_driver.open()
            config = '\n'.join(self.content.splitlines())
            getattr(napalm_driver, self.action)(config=config)
            napalm_driver.commit_config()
            napalm_driver.close()
        except Exception as e:
            result = f'napalm config did not work because of {e}'
            success = False
        else:
            result = f'configuration OK:\n\n{config}'
            success = True
        return success, result, incoming_payload


service_classes['Napalm Configuration Service'] = NapalmConfigurationService
