from datetime import datetime
from sqlalchemy import Boolean, Column, Integer, String, Text
from sqlalchemy.orm import relationship
from typing import List

from eNMS.database import SMALL_STRING_LENGTH, LARGE_STRING_LENGTH
from eNMS.database.associations import job_event_table, event_syslog_table
from eNMS.database.base import AbstractBase


class Syslog(AbstractBase):

    __tablename__ = type = "Syslog"
    id = Column(Integer, primary_key=True)
    time = Column(String(SMALL_STRING_LENGTH), default="")
    origin = Column(Text(LARGE_STRING_LENGTH), default="")
    content = Column(Text(LARGE_STRING_LENGTH), default="")
    events = relationship("Event", secondary=event_syslog_table, back_populates="syslogs")

    def update(self, **kwargs: str) -> None:
        kwargs["time"] = str(datetime.now())
        super().update(**kwargs)

    def generate_row(self, table: str) -> List[str]:
        return []


class ChangeLog(AbstractBase):

    __tablename__ = type = "ChangeLog"
    id = Column(Integer, primary_key=True)
    time = Column(String(SMALL_STRING_LENGTH), default="")
    severity = Column(String(SMALL_STRING_LENGTH), default="N/A")
    content = Column(Text(LARGE_STRING_LENGTH), default="")

    def update(self, **kwargs: str) -> None:
        kwargs["time"] = str(datetime.now())
        super().update(**kwargs)

    def generate_row(self, table: str) -> List[str]:
        return []


class Event(AbstractBase):

    __tablename__ = type = "Event"
    id = Column(Integer, primary_key=True)
    name = Column(String(SMALL_STRING_LENGTH), unique=True)
    origin = Column(String(SMALL_STRING_LENGTH), default="")
    origin_regex = Column(Boolean, default=False)
    name = Column(String(SMALL_STRING_LENGTH), default="")
    content_regex = Column(Boolean, default=False)
    syslogs = relationship("Syslog", secondary=event_syslog_table, back_populates="events")
    jobs = relationship("Job", secondary=job_event_table, back_populates="events")

    def generate_row(self, table: str) -> List[str]:
        return [
            f"""<button type="button" class="btn btn-info btn-xs"
            onclick="showTypePanel('event', '{self.id}')">
            Edit</button>""",
            f"""<button type="button" class="btn btn-danger btn-xs"
            onclick="deleteInstance('event', '{self.id}', '{self.name}')">
            Delete</button>""",
        ]
