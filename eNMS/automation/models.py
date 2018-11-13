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
from eNMS.base.helpers import fetch
from eNMS.base.models import Base


class Job(Base):

    __tablename__ = 'Job'
    type = Column(String)
    __mapper_args__ = {'polymorphic_identity': 'Job', 'polymorphic_on': type}
    id = Column(Integer, primary_key=True)
    hidden = Column(Boolean, default=False)
    name = Column(String, unique=True)
    description = Column(String)
    number_of_retries = Column(Integer, default=0)
    time_between_retries = Column(Integer, default=10)
    positions = Column(MutableDict.as_mutable(PickleType), default={})
    logs = Column(MutableDict.as_mutable(PickleType), default={})
    status = Column(String, default='Idle')
    state = Column(MutableDict.as_mutable(PickleType), default={})
    tasks = relationship('Task', back_populates='job', cascade='all,delete')
    vendor = Column(String)
    operating_system = Column(String)
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
    send_notification = Column(Boolean, default=False)
    send_notification_method = Column(
        String,
        default='mail_feedback_notification'
    )
    mail_recipient = Column(String)

    def compute_targets(self):
        targets = set(self.devices)
        for pool in self.pools:
            targets |= set(pool.devices)
        return targets

    def job_sources(self, workflow, subtype='all'):
        return [
            x.source for x in self.sources
            if (subtype == 'all' or x.subtype == subtype)
            and x.workflow == workflow
        ]

    def job_successors(self, workflow, subtype='all'):
        return [
            x.destination for x in self.destinations
            if (subtype == 'all' or x.subtype == subtype)
            and x.workflow == workflow
        ]

    def try_run(self, payload=None, remaining_targets=None):
        failed_attempts, now = {}, str(datetime.now()).replace(' ', '-')
        for i in range(self.number_of_retries + 1):
            results, remaining_targets = self.run(payload, remaining_targets)
            if results['success']:
                break
            if i != self.number_of_retries:
                failed_attempts[f'Attempts {i + 1}'] = results
                sleep(self.time_between_retries)
        results['failed_attempts'] = failed_attempts
        self.logs[now] = results
        return results, now

    def get_results(self, payload, device=None):
        try:
            return self.job(device, payload) if device else self.job(payload)
        except Exception as e:
            return {'success': False, 'result': str(e)}

    def run(self, payload=None, targets=None):
        if not targets:
            targets = self.compute_targets()
        if targets:
            results = {'result': {'devices': {}}}
            if self.multiprocessing:
                pool = ThreadPool(processes=min(len(targets), 1))
                pool.map(
                    self.device_run,
                    [(device, results, payload) for device in targets]
                )
                pool.close()
                pool.join()
            else:
                results['result']['devices'] = {
                    device.name: self.get_results(payload, device)
                    for device in targets
                }
            remaining_targets = {
                device for device in targets
                if not results['result']['devices'][device.name]['success']
            }
            results['success'] = not bool(remaining_targets)
            return results, remaining_targets
        else:
            return self.get_results(payload), None

    def device_run(self, args):
        device, results, payload = args
        device_result = self.get_results(payload, device)
        results['result']['devices'][device.name] = device_result


class Service(Job):

    __tablename__ = 'Service'
    id = Column(Integer, ForeignKey('Job.id'), primary_key=True)
    __mapper_args__ = {'polymorphic_identity': 'Service'}


class WorkflowEdge(Base):

    __tablename__ = type = 'WorkflowEdge'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    subtype = Column(Boolean)
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


class Workflow(Job):

    __tablename__ = 'Workflow'
    __mapper_args__ = {'polymorphic_identity': 'Workflow'}
    id = Column(Integer, ForeignKey('Job.id'), primary_key=True)
    multiprocessing = Column(Boolean, default=False)
    jobs = relationship(
        'Job',
        secondary=job_workflow_table,
        back_populates='workflows'
    )
    edges = relationship('WorkflowEdge', back_populates='workflow')

    def __init__(self, **kwargs):
        end = fetch('Service', name='End')
        default = [fetch('Service', name='Start'), end]
        self.jobs.extend(default)
        super().__init__(**kwargs)
        end.positions[self.name] = (500, 0)

    def job(self, *args):
        device, payload = args if len(args) == 2 else (None, args)
        if not self.multiprocessing:
            self.state = {'jobs': {}}
            if device:
                self.state['current_device'] = device.name
            db.session.commit()
        jobs, visited = [self.jobs[0]], set()
        results = {'success': False}
        while jobs:
            job = jobs.pop()
            # We check that all predecessors of the job have been visited
            # to ensure that the job will receive the full payload.
            if any(node not in visited for node in job.job_sources(self)):
                continue
            visited.add(job)
            if not self.multiprocessing:
                self.state['current_job'] = job.get_properties()
                db.session.commit()
            job_results, _ = job.try_run(results, {device} if device else None)
            success = job_results['success']
            if not self.multiprocessing:
                self.state['jobs'][job.id] = success
                db.session.commit()
            for successor in job.job_successors(self, success):
                if successor not in visited:
                    jobs.append(successor)
                if successor == self.jobs[1]:
                    results['success'] = True
            results[job.name] = job_results
            sleep(job.waiting_time)
        return results
