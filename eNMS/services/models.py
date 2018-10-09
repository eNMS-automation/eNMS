from sqlalchemy import Column, ForeignKey, Integer, PickleType, String
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import relationship

from eNMS.base.associations import (
    service_device_table,
    service_pool_table,
    job_workflow_table
)
from eNMS.base.custom_base import CustomBase
from eNMS.base.properties import cls_to_properties


class Job(CustomBase):

    __tablename__ = 'Job'

    id = Column(Integer, primary_key=True)
    name = Column(String(120), unique=True)
    description = Column(String)
    positions = Column(MutableDict.as_mutable(PickleType), default={})
    logs = Column(MutableDict.as_mutable(PickleType), default={})
    tasks = relationship('Task', back_populates='job')
    type = Column(String)
    waiting_time = Column(Integer, default=0)
    workflows = relationship(
        'Workflow',
        secondary=job_workflow_table,
        back_populates='jobs'
    )

    __mapper_args__ = {
        'polymorphic_identity': 'Job',
        'polymorphic_on': type
    }

    def job_sources(self, workflow, type='all'):
        return [
            x.source for x in self.sources
            if (type == 'all' or x.type == type) and x.workflow == workflow
        ]

    def job_successors(self, workflow, type='all'):
        return [
            x.destination for x in self.destinations
            if (type == 'all' or x.type == type) and x.workflow == workflow
        ]

    def compute_targets(self):
        targets = set(self.devices)
        for pool in self.pools:
            targets |= set(pool.devices)
        return targets


class Service(Job):

    __tablename__ = 'Service'

    id = Column(Integer, ForeignKey('Job.id'), primary_key=True)
    device_multiprocessing = False
    private = {'id'}
    devices = relationship(
        'Device',
        secondary=service_device_table,
        back_populates='services'
    )
    pools = relationship(
        'Pool',
        secondary=service_pool_table,
        back_populates='services'
    )

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
        serialized_object['devices'] = [
            obj.properties for obj in getattr(self, 'devices')
        ]
        serialized_object['pools'] = [
            obj.properties for obj in getattr(self, 'pools')
        ]
        return serialized_object

    def run(self, workflow, workflow_results=None):
        try:
            results = self.job(self, workflow_results)
        except Exception as e:
            return {'success': False, 'result': str(e)}
        self.logs[str(datetime.now())] = results
        db.session.commit()
        return results

    @property
    def serialized(self):
        properties = self.properties
        properties['devices'] = [
            obj.properties for obj in getattr(self, 'devices')
        ]
        properties['pools'] = [
            obj.properties for obj in getattr(self, 'pools')
        ]
        properties['tasks'] = [
            obj.properties for obj in getattr(self, 'tasks')
        ]
        return properties


service_classes = {}
