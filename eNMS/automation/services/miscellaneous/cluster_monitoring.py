from sqlalchemy import Column, ForeignKey, Integer, PickleType
from sqlalchemy.ext.mutable import MutableDict

from eNMS.automation.models import Service
from eNMS.base.classes import service_classes
from eNMS.base.helpers import fetch_all


class ClusterMonitoringService(Service):

    __tablename__ = 'ClusterMonitoringService'

    id = Column(Integer, ForeignKey('Service.id'), primary_key=True)
    has_targets = False

    __mapper_args__ = {
        'polymorphic_identity': 'ClusterMonitoringService',
    }

    def job(self, device, _):
        for instance in fetch_all('Instance'):
            setattr(device, property, value)
        return {'success': True, 'result': 'properties updated'}


service_classes['ClusterMonitoringService'] = ClusterMonitoringService
