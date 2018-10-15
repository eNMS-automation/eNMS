from re import search
from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.orm import relationship

from eNMS.base.associations import task_log_rule_table
from eNMS.base.custom_base import CustomBase


class Log(CustomBase):

    __tablename__ = 'Log'

    id = Column(Integer, primary_key=True)
    source = Column(String)
    content = Column(String)

    def __init__(self, source, content):
        self.source = source
        self.content = content
        for log_rule in LogRule.query.all():
            trigger_tasks = all(
                getattr(log_rule, prop) in getattr(self, prop)
                if not getattr(log_rule, prop + 'regex')
                else search(getattr(log_rule, prop), getattr(self, prop))
                for prop in ('source', 'content') if getattr(log_rule, prop)
            )
            if trigger_tasks:
                for task in log_rule.tasks:
                    task.run()

    def __repr__(self):
        return self.content


class LogRule(CustomBase):

    __tablename__ = 'LogRule'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    source = Column(String)
    sourceregex = Column(Boolean)
    content = Column(String)
    contentregex = Column(Boolean)
    tasks = relationship(
        'Task',
        secondary=task_log_rule_table,
        back_populates='log_rules'
    )

    def __repr__(self):
        return self.content
