from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
from re import search
from sqlalchemy import Boolean, case, ForeignKey, Integer
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship
from typing import Any, List, Optional, Tuple

from eNMS import app
from eNMS.database import Session
from eNMS.database.dialect import Column, LargeString, MutableDict, SmallString
from eNMS.database.associations import (
    job_event_table,
    task_device_table,
    task_pool_table,
)
from eNMS.database.base import AbstractBase


class Task(AbstractBase):

    __tablename__ = type = "Task"
    id = Column(Integer, primary_key=True)
    aps_job_id = Column(SmallString)
    name = Column(SmallString, unique=True)
    description = Column(SmallString)
    creation_time = Column(SmallString)
    scheduling_mode = Column(SmallString, default="standard")
    periodic = Column(Boolean)
    frequency = Column(Integer)
    frequency_unit = Column(SmallString, default="seconds")
    start_date = Column(SmallString)
    end_date = Column(SmallString)
    crontab_expression = Column(SmallString)
    is_active = Column(Boolean, default=False)
    initial_payload = Column(MutableDict)
    devices = relationship(
        "Device", secondary=task_device_table, back_populates="tasks"
    )
    pools = relationship("Pool", secondary=task_pool_table, back_populates="tasks")
    job_id = Column(Integer, ForeignKey("Job.id"))
    job = relationship("Job", back_populates="tasks")
    job_name = association_proxy("job", "name")

    def __init__(self, **kwargs: Any) -> None:
        super().update(**kwargs)
        self.creation_time = app.get_time()  # type: ignore
        self.aps_job_id = kwargs.get("aps_job_id", self.creation_time)

    def update(self, **kwargs: Any) -> None:
        super().update(**kwargs)

    def generate_row(self, table: str) -> List[str]:
        status = "Pause" if self.is_active else "Resume"
        return [
            f"""<button id="pause-resume-{self.id}" type="button"
            class="btn btn-success btn-xs" onclick=
            "{status.lower()}Task('{self.id}')">{status}</button>""",
            f"""<button type="button" class="btn btn-primary btn-xs"
            onclick="showTypePanel('task', '{self.id}')">Edit</button>""",
            f"""<button type="button" class="btn btn-primary btn-xs"
            onclick="showTypePanel('task', '{self.id}', 'duplicate')">
            Duplicate</button>""",
            f"""<button type="button" class="btn btn-danger btn-xs"
            onclick="showDeletionPanel('task', '{self.id}', '{self.name}')">
            Delete</button>""",
        ]

    @hybrid_property
    def status(self) -> str:
        return "Active" if self.is_active else "Inactive"

    @status.expression  # type: ignore
    def status(cls) -> str:  # noqa: N805
        return case([(cls.is_active, "Active")], else_="Inactive")

    @property
    def next_run_time(self) -> Optional[str]:
        job = app.scheduler.get_job(self.aps_job_id)
        if job and job.next_run_time:
            return job.next_run_time.strftime("%Y-%m-%d %H:%M:%S")
        return None

    @property
    def time_before_next_run(self) -> Optional[str]:
        job = app.scheduler.get_job(self.aps_job_id)
        if job and job.next_run_time:
            delta = job.next_run_time.replace(tzinfo=None) - datetime.now()
            hours, remainder = divmod(delta.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            days = f"{delta.days} days, " if delta.days else ""
            return f"{days}{hours}h:{minutes}m:{seconds}s"
        return None

    def aps_conversion(self, date: str) -> str:
        dt: datetime = datetime.strptime(date, "%d/%m/%Y %H:%M:%S")
        return datetime.strftime(dt, "%Y-%m-%d %H:%M:%S")

    def aps_date(self, datetype: str) -> Optional[str]:
        date = getattr(self, datetype)
        return self.aps_conversion(date) if date else None

    def pause(self) -> None:
        app.scheduler.pause_job(self.aps_job_id)
        self.is_active = False  # type: ignore
        Session.commit()

    def resume(self) -> None:
        self.schedule()
        app.scheduler.resume_job(self.aps_job_id)
        self.is_active = True  # type: ignore
        Session.commit()

    def delete_task(self) -> None:
        if app.scheduler.get_job(self.aps_job_id):
            app.scheduler.remove_job(self.aps_job_id)
        Session.commit()

    def run_properties(self) -> dict:
        properties = {"payload": self.initial_payload, "task": self.id}
        if self.devices:
            properties["devices"] = [  # type: ignore
                device.id for device in self.devices
            ]
        if self.pools:
            properties["pools"] = [pool.id for pool in self.pools]  # type: ignore
        return properties

    def kwargs(self) -> Tuple[dict, dict]:
        default = {
            "id": self.aps_job_id,
            "func": app.run,
            "replace_existing": True,
            "args": [self.job.id],
            "kwargs": self.run_properties(),
        }
        if self.scheduling_mode == "cron":
            self.periodic = True  # type: ignore
            expression = self.crontab_expression.split()
            mapping = {
                "0": "sun",
                "1": "mon",
                "2": "tue",
                "3": "wed",
                "4": "thu",
                "5": "fri",
                "6": "sat",
                "7": "sun",
            }
            expression[-1] = ",".join(mapping[day] for day in expression[-1].split(","))
            trigger = {"trigger": CronTrigger.from_crontab(" ".join(expression))}
        elif self.frequency:
            self.periodic = True  # type: ignore
            frequency_in_seconds = (
                int(self.frequency)
                * {"seconds": 1, "minutes": 60, "hours": 3600, "days": 86400}[
                    self.frequency_unit
                ]
            )
            trigger = {
                "trigger": "interval",
                "start_date": self.aps_date("start_date"),
                "end_date": self.aps_date("end_date"),
                "seconds": frequency_in_seconds,
            }
        else:
            self.periodic = False  # type: ignore
            trigger = {"trigger": "date", "run_date": self.aps_date("start_date")}
        return default, trigger

    def schedule(self) -> None:
        default, trigger = self.kwargs()
        if not app.scheduler.get_job(self.aps_job_id):
            app.scheduler.add_job(**{**default, **trigger})
        else:
            app.scheduler.reschedule_job(default.pop("id"), **trigger)


class Baselog(AbstractBase):

    __tablename__ = "Baselog"
    type = Column(SmallString)
    __mapper_args__ = {"polymorphic_identity": "Baselog", "polymorphic_on": type}
    id = Column(Integer, primary_key=True)
    time = Column(SmallString)
    content = Column(LargeString, default="")

    def update(self, **kwargs: str) -> None:
        kwargs["time"] = str(datetime.now())
        super().update(**kwargs)

    def generate_row(self, table: str) -> List[str]:
        return []


class Syslog(Baselog):

    __tablename__ = "Syslog"
    __mapper_args__ = {"polymorphic_identity": "Syslog"}
    parent_cls = "Baselog"
    id = Column(Integer, ForeignKey("Baselog.id"), primary_key=True)
    source = Column(LargeString, default="")


class Changelog(Baselog):

    __tablename__ = "Changelog"
    __mapper_args__ = {"polymorphic_identity": "Changelog"}
    parent_cls = "Baselog"
    id = Column(Integer, ForeignKey("Baselog.id"), primary_key=True)
    severity = Column(SmallString, default="N/A")
    user = Column(LargeString, default="")


class Event(AbstractBase):

    __tablename__ = type = "Event"
    id = Column(Integer, primary_key=True)
    name = Column(SmallString, unique=True)
    log_source = Column(SmallString)
    log_source_regex = Column(Boolean, default=False)
    log_content = Column(SmallString)
    log_content_regex = Column(Boolean, default=False)
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

    def match_log(self, source: str, content: str) -> None:
        source_match = (
            search(self.log_source, source)
            if self.log_source_regex
            else self.log_source in source
        )
        content_match = (
            search(self.log_content, content)
            if self.log_content_regex
            else self.log_content in content
        )
        if source_match and content_match:
            for job in self.jobs:
                job.run()
