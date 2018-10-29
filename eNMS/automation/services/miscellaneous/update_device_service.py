from sqlalchemy import Column, ForeignKey, Integer, PickleType
from sqlalchemy.ext.mutable import MutableDict

from eNMS.automation.models import Service
from eNMS.base.models import service_classes


class UpdateInventoryService(Service):

    __tablename__ = 'UpdateInventoryService'

    id = Column(Integer, ForeignKey('Service.id'), primary_key=True)
    update_dictionnary = Column(MutableDict.as_mutable(PickleType), default={})

    __mapper_args__ = {
        'polymorphic_identity': 'update_inventory_service',
    }

    def job(self, device, payload):
        for property, value in self.update_dictionnary.items():
            setattr(device, property, value)
        return {'success': True, 'result': 'properties updated'}


service_classes['update_inventory_service'] = UpdateInventoryService
