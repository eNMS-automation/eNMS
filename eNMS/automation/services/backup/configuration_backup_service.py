from datetime import datetime
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String

from eNMS.automation.models import Service
from eNMS.base.classes import service_classes


class ConfigurationBackupService(Service):

    __tablename__ = 'ConfigurationBackupService'

    id = Column(Integer, ForeignKey('Service.id'), primary_key=True)
    has_targets = True

    __mapper_args__ = {
        'polymorphic_identity': 'ConfigurationBackupService',
    }

    def job(self, device, _):

        return {
            'success': True,
            'result': f'logs stored in {destination} ({device.ip_address})'
        }


service_classes['ConfigurationBackupService'] = ConfigurationBackupService
