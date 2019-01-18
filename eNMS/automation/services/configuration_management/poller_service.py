from sqlalchemy import Column, ForeignKey, Integer

from eNMS.automation.models import Service
from eNMS.base.classes import service_classes


class PollerService(Service):

    __tablename__ = 'PollerService'

    id = Column(Integer, ForeignKey('Service.id'), primary_key=True)
    has_targets = True

    __mapper_args__ = {
        'polymorphic_identity': 'PollerService',
    }

    def job(self, device, _):
        
        return {
            'success': True,
            'result': 'success'
        }


service_classes['PollerService'] = PollerService
