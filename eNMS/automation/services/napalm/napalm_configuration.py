from sqlalchemy import Column, ForeignKey, Integer, PickleType, String
from sqlalchemy.ext.mutable import MutableDict

from eNMS.automation.helpers import (
    napalm_connection,
    NAPALM_DRIVERS,
    substitute
)
from eNMS.automation.models import Service, service_classes


class NapalmConfigurationService(Service):

    __tablename__ = 'NapalmConfigurationService'

    id = Column(Integer, ForeignKey('Service.id'), primary_key=True)
    has_targets = True
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

    def job(self, device, results, payload):
        napalm_driver = napalm_connection(self, device)
        napalm_driver.open()
        config = '\n'.join(substitute(self.content, locals()).splitlines())
        getattr(napalm_driver, self.action)(config=config)
        napalm_driver.commit_config()
        napalm_driver.close()
        return {'success': True, 'result': f'Config push ({config})'}


service_classes['napalm_configuration_service'] = NapalmConfigurationService
