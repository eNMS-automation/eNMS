from sqlalchemy import Column, ForeignKey, Integer, PickleType, String
from sqlalchemy.ext.mutable import MutableDict

from eNMS.automation.helpers import (
    napalm_connection,
    NAPALM_DRIVERS,
    substitute
)
from eNMS.automation.models import Service
from eNMS.base.classes import service_classes


class NapalmConfigurationService(Service):

    __tablename__ = 'NapalmConfigurationService'

    id = Column(Integer, ForeignKey('Service.id'), primary_key=True)
    multiprocessing = True
    action = Column(String)
    action_values = (
        ('load_merge_candidate', 'Load merge'),
        ('load_replace_candidate', 'Load replace')
    )
    content = Column(String)
    content_textarea = True
    driver = Column(String)
    driver_values = NAPALM_DRIVERS
    optional_args = Column(MutableDict.as_mutable(PickleType), default={})

    __mapper_args__ = {
        'polymorphic_identity': 'NapalmConfigurationService',
    }

    def job(self, device, payload):
        napalm_driver = napalm_connection(self, device)
        napalm_driver.open()
        config = '\n'.join(substitute(self.content, locals()).splitlines())
        getattr(napalm_driver, self.action)(config=config)
        napalm_driver.commit_config()
        napalm_driver.close()
        return {'success': True, 'result': f'Config push ({config})'}


service_classes['NapalmConfigurationService'] = NapalmConfigurationService
