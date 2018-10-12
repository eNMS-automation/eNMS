from sqlalchemy import Column, ForeignKey, Integer, PickleType
from sqlalchemy.ext.mutable import MutableDict

from eNMS.automation.models import Service, service_classes


class UpdateDeviceService(Service):

    __tablename__ = 'UpdateDeviceService'

    id = Column(Integer, ForeignKey('Service.id'), primary_key=True)
    update_dictionnary = Column(MutableDict.as_mutable(PickleType), default={})

    __mapper_args__ = {
        'polymorphic_identity': 'update_device_service',
    }

    def job(self, device, results, payload):
        for property, value in self.update_dictionnary.items():
            setattr(device, property, value)
        return {'success': True, 'result': 'properties updated'}


service_classes['update_device_service'] = UpdateDeviceService
