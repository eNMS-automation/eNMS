from sqlalchemy import Column, ForeignKey, Integer, Table

from eNMS.base.custom_base import CustomBase


inner_task_node_table = Table(
    'inner_task_node_association',
    CustomBase.metadata,
    Column('node_id', Integer, ForeignKey('Node.id')),
    Column('inner_task_id', Integer, ForeignKey('InnerTask.id'))
)

scheduled_task_node_table = Table(
    'scheduled_task_node_association',
    CustomBase.metadata,
    Column('node_id', Integer, ForeignKey('Node.id')),
    Column('scheduled_script_task_id', Integer, ForeignKey('ScheduledScriptTask.id'))
)

inner_task_script_table = Table(
    'inner_task_script_association',
    CustomBase.metadata,
    Column('script_id', Integer, ForeignKey('Script.id')),
    Column('inner_task_id', Integer, ForeignKey('InnerTask.id'))
)

scheduled_task_script_table = Table(
    'scheduled_task_script_association',
    CustomBase.metadata,
    Column('script_id', Integer, ForeignKey('Script.id')),
    Column('scheduled_script_task_id', Integer, ForeignKey('ScheduledScriptTask.id'))
)

scheduled_task_log_rule_table = Table(
    'scheduled_task_log_rule_association',
    CustomBase.metadata,
    Column('scheduled_task_id', Integer, ForeignKey('ScheduledTask.id')),
    Column('log_rule_id', Integer, ForeignKey('LogRule.id'))
)

pool_node_table = Table(
    'pool_node_association',
    CustomBase.metadata,
    Column('pool_id', Integer, ForeignKey('Pool.id')),
    Column('node_id', Integer, ForeignKey('Node.id'))
)

pool_link_table = Table(
    'pool_link_association',
    CustomBase.metadata,
    Column('pool_id', Integer, ForeignKey('Pool.id')),
    Column('link_id', Integer, ForeignKey('Link.id'))
)
