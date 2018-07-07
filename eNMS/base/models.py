from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Table

from eNMS import db
from eNMS.base.properties import cls_to_properties


class CustomBase(db.Model):

    __abstract__ = True

    # simplifies the syntax for flask forms
    @classmethod
    def choices(cls):
        return [(obj.id, obj.name) for obj in cls.query.all()]

    def __repr__(self):
        return self.name

    def __lt__(self, other):
        return True

    @property
    def serialized(self):
        return {p: getattr(self, p) for p in cls_to_properties[self.__tablename__]}

    @classmethod
    def serialize(cls):
        return [obj.serialized for obj in cls.query.all()]


class Log(CustomBase):

    __tablename__ = 'Log'

    id = Column(Integer, primary_key=True)
    source = Column(String)
    content = Column(Boolean)

    def __init__(self, source, content):
        self.source = source
        self.content = content

    def __repr__(self):
        return self.content


class LogTriggeredTaskRule(CustomBase):

    __tablename__ = 'LogTriggeredTaskRule'

    id = Column(Integer, primary_key=True)
    content = Column(String)
    content_regex = Column(String)
    tasks = relationship(
        'ScheduledTask',
        secondary=scheduled_task_log_rule_table,
        back_populates='log_rules'
    )

    def __init__(self, content, content_regex):
        self.content = content
        self.content_regex = content_regex


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
    Column('log_rule_id', Integer, ForeignKey('LogTriggeredTaskRule.id'))
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
