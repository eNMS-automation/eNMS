from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from eNMS.base.custom_base import CustomBase
from eNMS.base.properties import cls_to_properties


def multiprocessing(function):
    def wrapper(self, args):
        task, device, results, incoming_payload = args
        success, result, payload = function(self, *args)
        if 'logs' in results:
            results['logs'][device.name] = result
            results['payload']['outgoing_payload'][device.name] = payload
        else:
            results['logs'] = {device.name: result}
            results['payload'] = {
                'incoming_payload': incoming_payload,
                'outgoing_payload': {device.name: payload}
            }
        if 'success' not in results or results['success']:
            results['success'] = success
    return wrapper


class Job(CustomBase):

    __tablename__ = 'Job'

    id = Column(Integer, primary_key=True)
    name = Column(String(120), unique=True)
    description = Column(String)
    type = Column(String)

    __mapper_args__ = {
        'polymorphic_identity': 'Job',
        'polymorphic_on': type
    }


class Service(Job):

    __tablename__ = 'Service'

    id = Column(Integer, ForeignKey('Job.id'), primary_key=True)
    tasks = relationship('ServiceTask', back_populates='service')
    device_multiprocessing = False
    private = {'id'}

    __mapper_args__ = {
        'polymorphic_identity': 'service',
    }

    @property
    def properties(self):
        return {p: getattr(self, p) for p in cls_to_properties['Service']}

    @property
    def column_values(self):
        serialized_object = self.properties
        for col in self.__table__.columns:
            value = getattr(self, col.key)
            serialized_object[col.key] = value
        return serialized_object

    @property
    def serialized(self):
        properties = self.properties
        properties['tasks'] = [
            obj.properties for obj in getattr(self, 'tasks')
        ]
        return properties


service_classes = {}



