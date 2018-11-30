from apscheduler.jobstores.base import JobLookupError
from datetime import datetime
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from eNMS import db, scheduler
from eNMS.automation.helpers import scheduler_job
from eNMS.base.models import Base


class Task(Base):

    __tablename__ = type = 'Task'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    description = Column(String)
    creation_time = Column(String)
    status = Column(String)
    periodic = Column(Boolean)
    frequency = Column(Integer)
    start_date = Column(String)
    end_date = Column(String)
    job_id = Column(Integer, ForeignKey('Job.id'))
    job = relationship('Job', back_populates='tasks')

    def __init__(self, **kwargs):
        super().update(**kwargs)
        self.status = 'Active'
        self.creation_time = str(datetime.now())
        self.schedule()

    def update(self, **kwargs):
        super().update(**kwargs)
        self.reschedule()

    @property
    def job_name(self):
        return self.job.name

    def aps_conversion(self, date):
        dt = datetime.strptime(date, '%d/%m/%Y %H:%M:%S')
        return datetime.strftime(dt, '%Y-%m-%d %H:%M:%S')

    def aps_date(self, datetype):
        date = getattr(self, datetype)
        return self.aps_conversion(date) if date else None

    def pause_task(self):
        scheduler.pause_job(self.creation_time)
        self.status = 'Suspended'
        db.session.commit()

    def resume_task(self):
        scheduler.resume_job(self.creation_time)
        self.status = 'Active'
        db.session.commit()

    def delete_task(self):
        try:
            scheduler.delete_job(self.creation_time)
        except JobLookupError:
            pass
        db.session.commit()

    def kwargs(self):
        if self.frequency:
            return {
                'trigger': 'interval',
                'start_date': self.aps_date('start_date'),
                'end_date': self.aps_date('end_date'),
                'seconds': self.frequency
            }
        else:
            return {
                'trigger': 'date',
                'run_date': self.aps_date('start_date')
            }

    def schedule(self):
        if self.frequency:
            scheduler.add_job(
                id=self.creation_time,
                func=scheduler_job,
                args=[self.job.id, self.creation_time],
                replace_existing=True
                
            )
        else:
            scheduler.add_job(
                id=self.creation_time,
                func=scheduler_job,
                run_date=self.aps_date('start_date'),
                args=[self.job.id, self.creation_time],
                trigger='date',
                replace_existing=True
            )

    def reschedule(self):
        if self.frequency:
            scheduler.add_job(
                id=self.creation_time,
                func=scheduler_job,
                args=[self.job.id, self.creation_time],
                trigger='interval',
                start_date=self.aps_date('start_date'),
                end_date=self.aps_date('end_date'),
                seconds=int(self.frequency),
                replace_existing=True
            )
        else:
            scheduler.add_job(
                id=self.creation_time,
                func=scheduler_job,
                run_date=self.aps_date('start_date'),
                args=[self.job.id, self.creation_time],
                trigger='date',
                replace_existing=True
            )
