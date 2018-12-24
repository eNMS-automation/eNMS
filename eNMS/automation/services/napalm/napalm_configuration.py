from sqlalchemy import (
    Boolean,
    Column,
    ForeignKey,
    Integer,
    PickleType,
    String
)
from sqlalchemy.ext.mutable import MutableDict

from eNMS.automation.helpers import NAPALM_DRIVERS
from eNMS.automation.models import Service
from eNMS.base.classes import service_classes


class NapalmConfigurationService(Service):

    __tablename__ = 'NapalmConfigurationService'

    id = Column(Integer, ForeignKey('Service.id'), primary_key=True)
    has_targets = True
    action = Column(String)
    action_values = (
        ('load_merge_candidate', 'Load merge'),
        ('load_replace_candidate', 'Load replace')
    )
    content = Column(String)
    content_textarea = True
    driver = Column(String)
    driver_values = NAPALM_DRIVERS
    use_device_driver = Column(Boolean, default=True)
    optional_args = Column(MutableDict.as_mutable(PickleType), default={})

    __mapper_args__ = {
        'polymorphic_identity': 'NapalmConfigurationService',
    }

    def job(self, device, _):
        napalm_driver = self.napalm_connection(device)
        napalm_driver.open()
        config = '\n'.join(self.sub(self.content, locals()).splitlines())
        getattr(napalm_driver, self.action)(config=config)
        napalm_driver.commit_config()
        napalm_driver.close()
        return {'success': True, 'result': f'Config push ({config})'}


service_classes['NapalmConfigurationService'] = NapalmConfigurationService
