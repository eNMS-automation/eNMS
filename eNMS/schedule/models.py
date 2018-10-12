from apscheduler.jobstores.base import JobLookupError
from datetime import datetime
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from eNMS import db, scheduler
from eNMS.automation.helpers import scheduler_job
from eNMS.base.associations import task_log_rule_table
from eNMS.base.custom_base import CustomBase
from eNMS.base.properties import cls_to_properties


class Task(CustomBase):

    __tablename__ = 'Task'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    creation_time = Column(String)
    status = Column(String)
    type = Column(String)
    user_id = Column(Integer, ForeignKey('User.id'))
    user = relationship('User', back_populates='tasks')
    frequency = Column(String)
    start_date = Column(String)
    end_date = Column(String)
    job_id = Column(Integer, ForeignKey('Job.id'))
    job = relationship('Job', back_populates='tasks')
    log_rules = relationship(
        'LogRule',
        secondary=task_log_rule_table,
        back_populates='tasks'
    )

    __mapper_args__ = {
        'polymorphic_identity': 'Task',
        'polymorphic_on': type
    }

    def __init__(self, **kwargs):
        self.job = kwargs.pop('job')
        self.update(**kwargs)
        self.status = 'Active'
        self.creation_time = str(datetime.now())
        self.is_active = True
        self.schedule()

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

    def schedule(self):
        if self.frequency:
            scheduler.add_job(
                id=self.creation_time,
                func=scheduler_job,
                args=[self.name],
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
                args=[self.name],
                trigger='date',
                replace_existing=True
            )
        return str(datetime.now())

    @property
    def properties(self):
        return {p: getattr(self, p) for p in cls_to_properties['Task']}

    @property
    def serialized(self):
        properties = self.properties
        properties['job'] = self.job.properties
        return properties
