from sqlalchemy import Column, ForeignKey, Integer, PickleType, String
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import relationship

from eNMS.base.associations import (
    job_device_table,
    job_pool_table,
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
    scheduled_tasks = relationship('Task', back_populates='job')
    type = Column(String)
    waiting_time = Column(Integer, default=0)
    workflows = relationship(
        'Workflow',
        secondary=job_workflow_table,
        back_populates='jobs'
    )
    devices = relationship(
        'Device',
        secondary=job_device_table,
        back_populates='jobs'
    )
    pools = relationship(
        'Pool',
        secondary=job_pool_table,
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

    def run(self, workflow, workflow_results=None):
        try:
            results = self.job.job(self, workflow_results)
        except Exception as e:
            return {'success': False, 'result': str(e)}
        self.job.logs[str(datetime.now())] = results
        db.session.commit()
        return results

    @property
    def serialized(self):
        properties = self.properties
        properties['scheduled_tasks'] = [
            obj.properties for obj in getattr(self, 'scheduled_tasks')
        ]
        return properties


service_classes = {}
