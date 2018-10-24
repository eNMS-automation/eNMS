from datetime import datetime
from multiprocessing.pool import ThreadPool
from sqlalchemy import Boolean, Column, ForeignKey, Integer, PickleType, String
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import backref, relationship
from time import sleep

from eNMS import db
from eNMS.base.associations import (
    job_device_table,
    job_log_rule_table,
    job_pool_table,
    job_workflow_table
)
from eNMS.base.helpers import retrieve
from eNMS.base.custom_base import CustomBase
from eNMS.base.properties import cls_to_properties


class Job(CustomBase):

    __tablename__ = 'Job'

    id = Column(Integer, primary_key=True)
    name = Column(String(120), unique=True)
    description = Column(String)
    number_of_retry = Column(Integer, default=1)
    time_between_retries = Column(Integer, default=10)
    positions = Column(MutableDict.as_mutable(PickleType), default={})
    logs = Column(MutableDict.as_mutable(PickleType), default={})
    tasks = relationship('Task', back_populates='job', cascade='all,delete')
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
    log_rules = relationship(
        'LogRule',
        secondary=job_log_rule_table,
        back_populates='jobs'
    )

    __mapper_args__ = {
        'polymorphic_identity': 'Job',
        'polymorphic_on': type
    }

    def compute_targets(self):
        targets = set(self.devices)
        for pool in self.pools:
            targets |= set(pool.devices)
        return targets

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

    def try_run(self, payload=None, targets=None):
        now = str(datetime.now())
        for i in range(self.number_of_retry):
            results = self.run(payload, targets)
            self.logs[now] = results
            if results['success']:
                break
            if i != self.number_of_retry - 1:
                sleep(self.time_between_retries)
        return results

    def run(self, payload=None, targets=None):
        if self.multiprocessing:
            # payload and targets come from the workflow.
            # if the service is run outside the context of a workflow, we use
            # the services targets
            # if it runs inside a workflow, and the workflow has devices of
            # its own, targets will be set to the workflow devices
            if not targets:
                targets = self.compute_targets()
            results = {'success': True, 'devices': {}}
            pool = ThreadPool(processes=min(len(targets), 1))
            pool.map(
                self.device_run,
                [(device, results, payload) for device in targets]
            )
            pool.close()
            pool.join()
        else:
            try:
                results = self.job(payload)
            except Exception as e:
                results = {'success': False, 'result': str(e)}
        return results

    def device_run(self, args):
        device, results, payload = args
        try:
            results['devices'][device.name] = self.job(device, payload)
        except Exception as e:
            results['devices'][device.name] = {
                'success': False,
                'result': str(e)
            }
        if not results['devices'][device.name]['success']:
            results['success'] = False


class Service(Job):

    __tablename__ = 'Service'

    id = Column(Integer, ForeignKey('Job.id'), primary_key=True)
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
        serialized_object['devices'] = [
            obj.properties for obj in getattr(self, 'devices')
        ]
        serialized_object['pools'] = [
            obj.properties for obj in getattr(self, 'pools')
        ]
        return serialized_object

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


class WorkflowEdge(CustomBase):

    __tablename__ = 'WorkflowEdge'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    type = Column(Boolean)
    source_id = Column(Integer, ForeignKey('Job.id'))
    source = relationship(
        'Job',
        primaryjoin='Job.id == WorkflowEdge.source_id',
        backref=backref('destinations', cascade='all, delete-orphan'),
        foreign_keys='WorkflowEdge.source_id'
    )
    destination_id = Column(Integer, ForeignKey('Job.id'))
    destination = relationship(
        'Job',
        primaryjoin='Job.id == WorkflowEdge.destination_id',
        backref=backref('sources', cascade='all, delete-orphan'),
        foreign_keys='WorkflowEdge.destination_id'
    )
    workflow_id = Column(Integer, ForeignKey('Workflow.id'))
    workflow = relationship(
        'Workflow',
        back_populates='edges',
        foreign_keys='WorkflowEdge.workflow_id'
    )

    @property
    def serialized(self):
        properties = self.properties
        properties['source'] = self.source.serialized
        properties['destination'] = self.destination.serialized
        return properties


class Workflow(Job):

    __tablename__ = 'Workflow'

    id = Column(Integer, ForeignKey('Job.id'), primary_key=True)
    multiprocessing = Column(Boolean, default=False)
    vendor = Column(String)
    operating_system = Column(String)
    status = Column(
        MutableDict.as_mutable(PickleType),
        default={'status': 'Idle'}
    )
    jobs = relationship(
        'Job',
        secondary=job_workflow_table,
        back_populates='workflows'
    )
    edges = relationship('WorkflowEdge', back_populates='workflow')

    __mapper_args__ = {
        'polymorphic_identity': 'workflow',
    }

    def __init__(self, **kwargs):
        self.jobs.extend([
            retrieve(Service, name='Start'),
            retrieve(Service, name='End')
        ])
        
        super().__init__(**kwargs)

    def job(self, *args):
        self.status = {'status': 'Running', 'jobs': {}}
        db.session.commit()
        device, payload = args if len(args) == 2 else (None, args)
        jobs, visited = [retrieve(Service, name='Start')], set()
        results = {'success': False}
        while jobs:
            job = jobs.pop()
            # We check that all predecessors of the job have been visited
            # to ensure that the job will receive the full payload.
            # If it isn't the case, we put it back in the heap and move on to
            # another job.
            if any(n not in visited for n in job.job_sources(self)):
                continue
            visited.add(job)
            self.status['current_job'] = job.serialized
            db.session.commit()
            job_results = job.run(results, {device} if device else None)
            success = job_results['success']
            self.status['jobs'][job.id] = success
            db.session.commit()
            if job == retrieve(Service, name='End'):
                results['success'] = success
            for successor in job.job_successors(self, success):
                if successor not in visited:
                    jobs.append(successor)
            results[job.name] = job_results
            sleep(job.waiting_time)
        db.session.commit()
        return results

    @property
    def serialized(self):
        properties = self.properties
        properties['tasks'] = [
            obj.properties for obj in getattr(self, 'tasks')
        ]
        properties['jobs'] = [
            obj.properties for obj in getattr(self, 'jobs')
        ]
        properties['edges'] = [edge.serialized for edge in self.edges]
        properties['devices'] = [
            obj.properties for obj in getattr(self, 'devices')
        ]
        properties['pools'] = [
            obj.properties for obj in getattr(self, 'pools')
        ]
        return properties
