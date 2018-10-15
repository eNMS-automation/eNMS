from datetime import datetime
from multiprocessing.pool import ThreadPool
from sqlalchemy import Boolean, Column, ForeignKey, Integer, PickleType, String
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import backref, relationship
from time import sleep

from eNMS.base.associations import (
    job_device_table,
    job_pool_table,
    job_workflow_table,
    task_log_rule_table
)
from eNMS.base.custom_base import CustomBase
from eNMS.base.properties import cls_to_properties


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
