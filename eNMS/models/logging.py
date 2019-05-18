from datetime import datetime
from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.orm import relationship
from typing import List

from eNMS.database import SMALL_STRING_LENGTH, LARGE_STRING_LENGTH
from eNMS.models.associations import job_log_rule_table, log_rule_log_table
from eNMS.database.base import AbstractBase


class Log(AbstractBase):

    __tablename__ = type = "Log"
    id = Column(Integer, primary_key=True)
    origin = Column(String(SMALL_STRING_LENGTH), default="")
    severity = Column(String(SMALL_STRING_LENGTH), default="N/A")
    content = Column(String(LARGE_STRING_LENGTH), default="")
    time = Column(String(SMALL_STRING_LENGTH), default="")
    log_rules = relationship(
        "LogRule", secondary=log_rule_log_table, back_populates="logs"
    )

    def update(self, **kwargs: str) -> None:
        kwargs["time"] = str(datetime.now())
        super().update(**kwargs)

    def generate_row(self, table: str) -> List[str]:
        return []


class LogRule(AbstractBase):

    __tablename__ = type = "LogRule"
    id = Column(Integer, primary_key=True)
    name = Column(String(SMALL_STRING_LENGTH), unique=True)
    origin = Column(String(SMALL_STRING_LENGTH), default="")
    origin_regex = Column(Boolean, default=False)
    name = Column(String(SMALL_STRING_LENGTH), default="")
    content_regex = Column(Boolean, default=False)
    logs = relationship("Log", secondary=log_rule_log_table, back_populates="log_rules")
    jobs = relationship("Job", secondary=job_log_rule_table, back_populates="log_rules")

    def generate_row(self, table: str) -> List[str]:
        return [
            f"""<button type="button" class="btn btn-info btn-xs"
            onclick="showTypePanel('logrule', '{self.id}')">
            Edit</button>""",
            f"""<button type="button" class="btn btn-danger btn-xs"
            onclick="deleteInstance('logrule', '{self.id}', '{self.name}')">
            Delete</button>""",
        ]
