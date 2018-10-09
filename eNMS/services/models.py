from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from eNMS.base.custom_base import CustomBase
from eNMS.base.properties import cls_to_properties


class Job(CustomBase):

    __tablename__ = 'Job'

    id = Column(Integer, primary_key=True)
    name = Column(String(120), unique=True)
    description = Column(String)
    task = relationship('Task', back_populates='job')
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
