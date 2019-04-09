from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
from sqlalchemy import Boolean, case, Column, ForeignKey, Integer, String
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship
from typing import Any, List, Optional, Tuple

from eNMS.extensions import db, scheduler
from eNMS.automation.functions import scheduler_job
from eNMS.models import Base


class Task(Base):

    __tablename__ = "Task"
    type = "Task"
    id = Column(Integer, primary_key=True)
    aps_job_id = Column(String(255))
    name = Column(String(255), unique=True)
    description = Column(String(255))
    creation_time = Column(String(255))
    scheduling_mode = Column(String(255), default="standard")
    periodic = Column(Boolean)
    frequency = Column(Integer)
    frequency_unit = Column(String(255), default="seconds")
    start_date = Column(String(255))
    end_date = Column(String(255))
    crontab_expression = Column(String(255))
    is_active = Column(Boolean, default=False)
    job_id = Column(Integer, ForeignKey("Job.id"))
    job = relationship("Job", back_populates="tasks")
    job_name = association_proxy("job", "name")

    def __init__(self, **kwargs: Any) -> None:
        super().update(**kwargs)
        self.creation_time = str(datetime.now())
        self.aps_job_id = kwargs.get("aps_job_id", self.creation_time)
        if self.is_active:
            self.schedule()

    def update(self, **kwargs: Any) -> None:
        super().update(**kwargs)
        if self.is_active:
            self.schedule()

    def generate_row(self, table: str) -> List[str]:
        status = "Pause" if self.is_active else "Resume"
        return [
            f"""<button id="pause-resume-{self.id}" type="button"
            class="btn btn-success btn-xs" onclick=
            "{status.lower()}Task('{self.id}')">{status}</button>""",
            f"""<button type="button" class="btn btn-primary btn-xs"
            onclick="showTypeModal('task', '{self.id}')">Edit</button>""",
            f"""<button type="button" class="btn btn-primary btn-xs"
            onclick="showTypeModal('task', '{self.id}', true)">
            Duplicate</button>""",
            f"""<button type="button" class="btn btn-danger btn-xs"
            onclick="confirmDeletion('task', '{self.id}')">
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
        job = scheduler.get_job(self.aps_job_id)
        if job and job.next_run_time:
            return job.next_run_time.strftime("%Y-%m-%d %H:%M:%S")
        return None

    @property
    def time_before_next_run(self) -> Optional[str]:
        job = scheduler.get_job(self.aps_job_id)
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
        scheduler.pause_job(self.aps_job_id)
        self.is_active = False
        db.session.commit()

    def resume(self) -> None:
        self.schedule()
        scheduler.resume_job(self.aps_job_id)
        self.is_active = True
        db.session.commit()

    def delete_task(self) -> None:
        if scheduler.get_job(self.aps_job_id):
            scheduler.remove_job(self.aps_job_id)
        db.session.commit()

    def kwargs(self) -> Tuple[dict, dict]:
        default = {
            "id": self.aps_job_id,
            "func": scheduler_job,
            "replace_existing": True,
            "args": [self.job.id, self.aps_job_id],
        }
        if self.scheduling_mode == "cron":
            self.periodic = True
            trigger = {"trigger": CronTrigger.from_crontab(self.crontab_expression)}
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

    def schedule(self) -> None:
        default, trigger = self.kwargs()
        if not scheduler.get_job(self.aps_job_id):
            scheduler.add_job(**{**default, **trigger})
        else:
            scheduler.reschedule_job(default.pop("id"), **trigger)
