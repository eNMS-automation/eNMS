from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
from flask_login import current_user
from re import search
from sqlalchemy import Boolean, case, ForeignKey, Integer
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship

from eNMS import app
from eNMS.database import db
from eNMS.models.base import AbstractBase


@db.set_custom_properties
class Task(AbstractBase):

    __tablename__ = type = "task"
    id = db.Column(Integer, primary_key=True)
    aps_job_id = db.Column(db.SmallString)
    name = db.Column(db.SmallString, unique=True)
    description = db.Column(db.SmallString)
    creation_time = db.Column(db.SmallString)
    scheduling_mode = db.Column(db.SmallString, default="standard")
    periodic = db.Column(Boolean)
    frequency = db.Column(Integer)
    frequency_unit = db.Column(db.SmallString, default="seconds")
    start_date = db.Column(db.SmallString)
    end_date = db.Column(db.SmallString)
    crontab_expression = db.Column(db.SmallString)
    is_active = db.Column(Boolean, default=False)
    initial_payload = db.Column(db.Dict)
    devices = relationship(
        "Device", secondary=db.task_device_table, back_populates="tasks"
    )
    pools = relationship("Pool", secondary=db.task_pool_table, back_populates="tasks")
    service_id = db.Column(Integer, ForeignKey("service.id"))
    service = relationship("Service", back_populates="tasks")
    service_name = association_proxy("service", "name")
    model_properties = ["next_run_time", "time_before_next_run", "status"]

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
        db.session.commit()

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
        db.session.commit()
        app.scheduler.pause_job(self.aps_job_id)

    def resume(self):
        self.schedule()
        app.scheduler.resume_job(self.aps_job_id)
        self.is_active = True
        db.session.commit()

    def run_properties(self):
        properties = {
            "task": self.id,
            "trigger": "Scheduler",
            "creator": current_user.name,
            **self.initial_payload,
        }
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
            "args": [self.service_id],
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
            app.scheduler.modify_job(
                default["id"], args=default["args"], kwargs=default["kwargs"]
            )
            app.scheduler.reschedule_job(default.pop("id"), **trigger)


@db.set_custom_properties
class Event(AbstractBase):

    __tablename__ = type = "event"
    id = db.Column(Integer, primary_key=True)
    name = db.Column(db.SmallString, unique=True)
    log_source = db.Column(db.SmallString)
    log_source_regex = db.Column(Boolean, default=False)
    log_content = db.Column(db.SmallString)
    log_content_regex = db.Column(Boolean, default=False)
    service_id = db.Column(Integer, ForeignKey("service.id"))
    service = relationship("Service", back_populates="events")
    service_name = association_proxy("service", "name")

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
