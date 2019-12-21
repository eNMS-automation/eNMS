from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
from re import search
from sqlalchemy import Boolean, case, ForeignKey, Integer
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship

from eNMS import app
from eNMS.database import Session
from eNMS.database.dialect import Column, LargeString, MutableDict, SmallString
from eNMS.database.associations import (
    task_device_table,
    task_pool_table,
)
from eNMS.database.base import AbstractBase


class Task(AbstractBase):

    __tablename__ = type = "task"
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
    service_id = Column(Integer, ForeignKey("service.id"))
    service = relationship("Service", back_populates="tasks")
    service_name = association_proxy("service", "name")

    def __init__(self, **kwargs):
        super().update(**kwargs)
        self.creation_time = app.get_time()
        self.aps_job_id = kwargs.get("aps_job_id", self.creation_time)
        if self.is_active:
            self.schedule()

    def update(self, **kwargs):
        super().update(**kwargs)
        if self.is_active:
            self.schedule()

    def delete(self):
        if app.scheduler.get_job(self.aps_job_id):
            app.scheduler.remove_job(self.aps_job_id)
        Session.commit()

    @hybrid_property
    def status(self):
        return "Active" if self.is_active else "Inactive"

    @status.expression
    def status(cls):  # noqa: N805
        return case([(cls.is_active, "Active")], else_="Inactive")

    @property
    def next_run_time(self):
        job = app.scheduler.get_job(self.aps_job_id)
        if job and job.next_run_time:
            return job.next_run_time.strftime("%Y-%m-%d %H:%M:%S")
        return None

    @property
    def time_before_next_run(self):
        job = app.scheduler.get_job(self.aps_job_id)
        if job and job.next_run_time:
            delta = job.next_run_time.replace(tzinfo=None) - datetime.now()
            hours, remainder = divmod(delta.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            days = f"{delta.days} days, " if delta.days else ""
            return f"{days}{hours}h:{minutes}m:{seconds}s"
        return None

    def aps_conversion(self, date):
        dt: datetime = datetime.strptime(date, "%d/%m/%Y %H:%M:%S")
        return datetime.strftime(dt, "%Y-%m-%d %H:%M:%S")

    def aps_date(self, datetype):
        date = getattr(self, datetype)
        return self.aps_conversion(date) if date else None

    def pause(self):
        self.is_active = False
        Session.commit()
        app.scheduler.pause_job(self.aps_job_id)

    def resume(self):
        self.schedule()
        app.scheduler.resume_job(self.aps_job_id)
        self.is_active = True
        Session.commit()

    def run_properties(self):
        properties = {"task": self.id, **self.initial_payload}
        if self.devices:
            properties["devices"] = [device.id for device in self.devices]
        if self.pools:
            properties["pools"] = [pool.id for pool in self.pools]
        return properties

    def kwargs(self):
        default = {
            "id": self.aps_job_id,
            "func": app.run,
            "replace_existing": True,
            "args": [self.service.id],
            "kwargs": self.run_properties(),
        }
        if self.scheduling_mode == "cron":
            self.periodic = True
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
                "*": "*",
            }
            expression[-1] = ",".join(mapping[day] for day in expression[-1].split(","))
            trigger = {"trigger": CronTrigger.from_crontab(" ".join(expression))}
        elif self.frequency:
            self.periodic = True
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
            self.periodic = False
            trigger = {"trigger": "date", "run_date": self.aps_date("start_date")}
        return default, trigger

    def schedule(self):
        default, trigger = self.kwargs()
        if not app.scheduler.get_job(self.aps_job_id):
            app.scheduler.add_job(**{**default, **trigger})
        else:
            app.scheduler.reschedule_job(default.pop("id"), **trigger)


class Changelog(AbstractBase):

    __tablename__ = "changelog"
    type = Column(SmallString)
    __mapper_args__ = {"polymorphic_identity": "changelog", "polymorphic_on": type}
    id = Column(Integer, primary_key=True)
    time = Column(SmallString)
    content = Column(LargeString, default="")
    severity = Column(SmallString, default="debug")
    user = Column(SmallString, default="admin")

    def update(self, **kwargs):
        kwargs["time"] = str(datetime.now())
        super().update(**kwargs)


class Event(AbstractBase):

    __tablename__ = type = "event"
    id = Column(Integer, primary_key=True)
    name = Column(SmallString, unique=True)
    log_source = Column(SmallString)
    log_source_regex = Column(Boolean, default=False)
    log_content = Column(SmallString)
    log_content_regex = Column(Boolean, default=False)
    service_id = Column(Integer, ForeignKey("service.id"))
    service = relationship("Service", back_populates="events")
    service_name = association_proxy("service", "name")

    def generate_row(self, **kwargs):
        return super().generate_row() + [
            f"""
            <ul class="pagination pagination-lg" style="margin: 0px; width: 150px">
          <li>
            <button type="button" class="btn btn-primary"
            onclick="eNMS.base.showTypePanel('event', '{self.id}')" data-tooltip="Edit"
              ><span class="glyphicon glyphicon-edit"></span
            ></button>
          </li>
          <li>
            <button type="button" class="btn btn-primary"
            onclick="eNMS.base.showTypePanel('event', '{self.id}', 'duplicate')"
            data-tooltip="Duplicate">
            <span class="glyphicon glyphicon-duplicate"></span></button>
          </li>
          <li>
            <button type="button" class="btn btn-danger"
            onclick="eNMS.base.showDeletionPanel({self.row_properties})" data-tooltip="Delete"
              ><span class="glyphicon glyphicon-trash"></span
            ></button>
          </li>
        </ul>"""
        ]

    def match_log(self, source, content):
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
            self.service.run()
