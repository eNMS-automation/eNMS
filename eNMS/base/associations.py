from sqlalchemy import Column, ForeignKey, Integer, Table

from eNMS.base.custom_base import CustomBase

job_device_table = Table(
    'job_device_association',
    CustomBase.metadata,
    Column('device_id', Integer, ForeignKey('Device.id')),
    Column('job_id', Integer, ForeignKey('Job.id'))
)

job_pool_table = Table(
    'job_pool_association',
    CustomBase.metadata,
    Column('pool_id', Integer, ForeignKey('Pool.id')),
    Column('job_id', Integer, ForeignKey('Job.id'))
)

task_log_rule_table = Table(
    'task_log_rule_association',
    CustomBase.metadata,
    Column('task_id', Integer, ForeignKey('Task.id')),
    Column('log_rule_id', Integer, ForeignKey('LogRule.id'))
)

job_workflow_table = Table(
    'job_workflow_association',
    CustomBase.metadata,
    Column('job_id', Integer, ForeignKey('Job.id')),
    Column('workflow_id', Integer, ForeignKey('Workflow.id'))
)

pool_device_table = Table(
    'pool_device_association',
    CustomBase.metadata,
    Column('pool_id', Integer, ForeignKey('Pool.id')),
    Column('device_id', Integer, ForeignKey('Device.id'))
)

pool_link_table = Table(
    'pool_link_association',
    CustomBase.metadata,
    Column('pool_id', Integer, ForeignKey('Pool.id')),
    Column('link_id', Integer, ForeignKey('Link.id'))
)
