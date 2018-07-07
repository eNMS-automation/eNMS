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
