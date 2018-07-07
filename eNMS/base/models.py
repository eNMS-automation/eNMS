from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.orm import relationship

from eNMS.base.associations import scheduled_task_log_rule_table
from eNMS.base.custom_base import CustomBase


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


class LogRule(CustomBase):

    __tablename__ = 'LogRule'

    id = Column(Integer, primary_key=True)
    content = Column(String)
    contentregex = Column(String)
    tasks = relationship(
        'ScheduledTask',
        secondary=scheduled_task_log_rule_table,
        back_populates='log_rules'
    )

    def __init__(self, **kwargs):
        self.content = kwargs['content'] 
        self.contentregex = 'contentregex' in kwargs
