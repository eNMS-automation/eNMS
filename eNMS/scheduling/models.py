from apscheduler.jobstores.base import JobLookupError
from datetime import datetime
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
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
        self.status = 'Pause'
        db.session.commit()

    def resume_task(self):
        scheduler.resume_job(self.creation_time)
        self.status = 'Active'
        db.session.commit()

    def delete_task(self):
        try:
            scheduler.remove_job(self.creation_time)
        except JobLookupError:
            pass
        db.session.commit()

    def kwargs(self):
        default = {
            'id': self.creation_time,
            'func': scheduler_job,
            'replace_existing': True,
            'args': [self.job.id, self.creation_time]
        }
        if self.frequency:
            self.periodic = True
            trigger = {
                'trigger': 'interval',
                'start_date': self.aps_date('start_date'),
                'end_date': self.aps_date('end_date'),
                'seconds': self.frequency
            }
        else:
            self.periodic = False
            trigger = {
                'trigger': 'date',
                'run_date': self.aps_date('start_date')
            }
        return default, trigger

    def schedule(self):
        default, trigger = self.kwargs()
        scheduler.add_job(**{**default, **trigger})

    def reschedule(self):
        if self.creation_time not in [job.id for job in scheduler.get_jobs()]:
            self.schedule()
        default, trigger = self.kwargs()
        scheduler.reschedule_job(default.pop('id'), **trigger)
