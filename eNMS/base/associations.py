from sqlalchemy import Column, ForeignKey, Integer, Table

from eNMS.base.custom_base import CustomBase

task_device_table = Table(
    'task_device_association',
    CustomBase.metadata,
    Column('device_id', Integer, ForeignKey('Device.id')),
    Column('script_task_id', Integer, ForeignKey('ScriptTask.id'))
)

task_pool_table = Table(
    'task_pool_association',
    CustomBase.metadata,
    Column('pool_id', Integer, ForeignKey('Pool.id')),
    Column('script_task_id', Integer, ForeignKey('ScriptTask.id'))
)

task_log_rule_table = Table(
    'task_log_rule_association',
    CustomBase.metadata,
    Column('task_id', Integer, ForeignKey('Task.id')),
    Column('log_rule_id', Integer, ForeignKey('LogRule.id'))
)

task_workflow_table = Table(
    'task_workflow_association',
    CustomBase.metadata,
    Column('task_id', Integer, ForeignKey('Task.id')),
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
