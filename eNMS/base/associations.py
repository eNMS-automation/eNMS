from sqlalchemy import Column, ForeignKey, Integer, Table

from eNMS.base.models import Base

job_device_table = Table(
    'job_device_association',
    Base.metadata,
    Column('device_id', Integer, ForeignKey('Device.id')),
    Column('job_id', Integer, ForeignKey('Job.id'))
)

job_pool_table = Table(
    'job_pool_association',
    Base.metadata,
    Column('pool_id', Integer, ForeignKey('Pool.id')),
    Column('job_id', Integer, ForeignKey('Job.id'))
)

log_rule_log_table = Table(
    'log_rule_log_association',
    Base.metadata,
    Column('log_id', Integer, ForeignKey('Log.id')),
    Column('log_rule_id', Integer, ForeignKey('LogRule.id'))
)

job_log_rule_table = Table(
    'job_log_rule_association',
    Base.metadata,
    Column('job_id', Integer, ForeignKey('Job.id')),
    Column('log_rule_id', Integer, ForeignKey('LogRule.id'))
)

job_workflow_table = Table(
    'job_workflow_association',
    Base.metadata,
    Column('job_id', Integer, ForeignKey('Job.id')),
    Column('workflow_id', Integer, ForeignKey('Workflow.id'))
)

pool_device_table = Table(
    'pool_device_association',
    Base.metadata,
    Column('pool_id', Integer, ForeignKey('Pool.id')),
    Column('device_id', Integer, ForeignKey('Device.id'))
)

pool_link_table = Table(
    'pool_link_association',
    Base.metadata,
    Column('pool_id', Integer, ForeignKey('Pool.id')),
    Column('link_id', Integer, ForeignKey('Link.id'))
)
