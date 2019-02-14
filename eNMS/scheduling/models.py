from datetime import datetime
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship
from typing import Any, Optional, Tuple

from eNMS.main import db, scheduler
from eNMS.automation.helpers import scheduler_job
from eNMS.base.models import Base


class Task(Base):

    __tablename__ = "Task"
    type = "Task"
    id = Column(Integer, primary_key=True)
    aps_job_id = Column(String)
    name = Column(String, unique=True)
    description = Column(String)
    creation_time = Column(String)
    status = Column(String)
    periodic = Column(Boolean)
    frequency = Column(Integer)
    start_date = Column(String)
    end_date = Column(String)
    job_id = Column(Integer, ForeignKey("Job.id"))
    job = relationship("Job", back_populates="tasks")
    job_name = association_proxy("job", "name")

    def __init__(self, **kwargs: Any) -> None:
        self.status = kwargs.pop("status", "Active")
        super().update(**kwargs)
        self.creation_time = str(datetime.now())
        self.aps_job_id = kwargs.get("aps_job_id", self.creation_time)
        if self.status == "Active":
            self.schedule()

    def update(self, **kwargs: Any) -> None:
        super().update(**kwargs)
        if self.status == "Active":
            self.schedule()

    def aps_conversion(self, date: str) -> str:
        dt: datetime = datetime.strptime(date, "%d/%m/%Y %H:%M:%S")
        return datetime.strftime(dt, "%Y-%m-%d %H:%M:%S")

    def aps_date(self, datetype: str) -> Optional[str]:
        date = getattr(self, datetype)
        return self.aps_conversion(date) if date else None

    def pause(self) -> None:
        scheduler.pause_job(self.aps_job_id)
        self.status = "Pause"
        db.session.commit()

    def resume(self) -> None:
        self.schedule()
        scheduler.resume_job(self.aps_job_id)
        self.status = "Active"
        db.session.commit()

    def delete_task(self) -> None:
        try:
            scheduler.remove_job(self.aps_job_id)
        except JobLookupError:
            pass
        db.session.commit()

    def kwargs(self) -> Tuple[dict, dict]:
        default = {
            "id": self.aps_job_id,
            "func": scheduler_job,
            "replace_existing": True,
            "args": [self.job.id, self.aps_job_id],
        }
        if self.frequency:
            self.periodic = True
            trigger = {
                "trigger": "interval",
                "start_date": self.aps_date("start_date"),
                "end_date": self.aps_date("end_date"),
                "seconds": int(self.frequency),
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

    @hybrid_property
    def next_run_time(self) -> Optional[str]:
        job = scheduler.get_job(self.aps_job_id)
        return job.next_run_time.strftime("%Y-%m-%d %H:%M:%S") if job else None

    @hybrid_property
    def time_before_next_run(self) -> Optional[str]:
        job = scheduler.get_job(self.aps_job_id)
        if not job:
            return ""
        else:
            delta = job.next_run_time.replace(tzinfo=None) - datetime.now()
            hours, remainder = divmod(delta.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            return f"{hours}h:{minutes}m:{seconds}s"
