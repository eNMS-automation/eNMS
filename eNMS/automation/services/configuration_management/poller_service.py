from sqlalchemy import Column, ForeignKey, Integer

from eNMS.automation.models import Service
from eNMS.base.classes import service_classes
from eNMS.base.helpers import fetch_all

class PollerService(Service):

    __tablename__ = 'PollerService'

    id = Column(Integer, ForeignKey('Service.id'), primary_key=True)
    has_targets = False

    __mapper_args__ = {
        'polymorphic_identity': 'PollerService',
    }

    def job(self, _):
        for service in fetch_all('Service'):
            if service.configuration_backup_service:
                service.try_run()
        return {
            'success': True,
            'result': 'success'
        }


service_classes['PollerService'] = PollerService
