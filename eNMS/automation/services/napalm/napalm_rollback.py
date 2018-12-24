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


class NapalmRollbackService(Service):

    __tablename__ = 'NapalmRollbackService'

    id = Column(Integer, ForeignKey('Service.id'), primary_key=True)
    has_targets = True
    driver = Column(String)
    driver_values = NAPALM_DRIVERS
    use_device_driver = Column(Boolean, default=True)
    optional_args = Column(MutableDict.as_mutable(PickleType), default={})

    __mapper_args__ = {
        'polymorphic_identity': 'NapalmRollbackService',
    }

    def job(self, device, _):
        napalm_driver = self.napalm_connection(device)
        napalm_driver.open()
        napalm_driver.rollback()
        napalm_driver.close()
        return {'success': True, 'result': 'Rollback successful'}


service_classes['NapalmRollbackService'] = NapalmRollbackService
