from base.database import db, get_obj
from base.models import (
    task_node_table,
    task_script_table,
    task_workflow_table,
    CustomBase
)
from datetime import datetime, timedelta
from flask_apscheduler import APScheduler
from multiprocessing.pool import ThreadPool
from sqlalchemy import Boolean, Column, Integer, String, PickleType
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import relationship

scheduler = APScheduler()

## Netmiko process and job


def job_multiprocessing(name):
    job_time = str(datetime.now())
    task = get_obj(Task, name=name)
    task.logs[job_time] = {}
    for task_job in task.scripts + task.workflows:
        results = {}
        pool = ThreadPool(processes=len(task.nodes))
        args = [(task, node, results) for node in task.nodes]
        pool.map(task_job.job, args)
        pool.close()
        pool.join()
        task.logs[job_time][task_job.name] = results
    db.session.commit()


## Tasks


class Task(CustomBase):

    __tablename__ = 'Task'

    id = Column(Integer, primary_key=True)
    recurrent = Column(Boolean, default=False)
    name = Column(String(120), unique=True)
    status = Column(String)
    creation_time = Column(Integer)
    logs = Column(MutableDict.as_mutable(PickleType), default={})
    nodes = relationship(
        "Node",
        secondary=task_node_table,
        back_populates="tasks"
    )
    scripts = relationship(
        "Script",
        secondary=task_script_table,
        back_populates="tasks"
    )
    workflows = relationship(
        "Workflow",
        secondary=task_workflow_table,
        back_populates="tasks"
    )
    user = relationship('User', back_populates='tasks', uselist=False)

    frequency = Column(String(120))
    start_date = Column(String)
    end_date = Column(String)
    creator = Column(String)

    properties = (
        'name',
        'start_date',
        'end_date',
        'frequency',
        'scripts',
        'workflows'
    )

    def __init__(self, **data):
        self.data = data
        self.name = data['name']
        self.nodes = data['nodes']
        self.user = data['user']
        self.scripts = data['scripts']
        self.workflows = data['workflows']
        self.frequency = data['frequency']
        self.recurrent = bool(self.frequency)
        self.creation_time = str(datetime.now())
        self.creator = data['user'].name
        self.status = 'active'
        # if the start date is left empty, we turn the empty string into
        # None as this is what AP Scheduler is expecting
        for date in ('start_date', 'end_date'):
            date = data[date]
            value = self.datetime_conversion(date) if date else None
            setattr(self, date, value)
        self.is_active = True
        if self.frequency:
            self.recurrent_scheduling()
        else:
            self.one_time_scheduling()

    @property
    def description(self):
        return '\n'.join([
            'Name: ' + self.name,
            'Frequency: {}s'.format(self.frequency),
            'Creation time: ' + self.creation_time,
            'Creator: ' + self.creator
        ])

    def datetime_conversion(self, date):
        dt = datetime.strptime(date, '%d/%m/%Y %H:%M:%S')
        return datetime.strftime(dt, '%Y-%m-%d %H:%M:%S')

    def pause_task(self):
        scheduler.pause_job(self.creation_time)
        self.status = 'suspended'
        db.session.commit()

    def resume_task(self):
        scheduler.resume_job(self.creation_time)
        self.status = "active"
        db.session.commit()

    def delete_task(self):
        scheduler.delete_job(self.creation_time)
        db.session.commit()

    def recurrent_scheduling(self):
        if not self.start_date:
            self.start_date = datetime.now() + timedelta(seconds=15)
        # run the job on a regular basis with an interval trigger
        scheduler.add_job(
            id=self.creation_time,
            func=job_multiprocessing,
            args=[self.name],
            trigger='interval',
            start_date=self.start_date,
            end_date=self.end_date,
            seconds=int(self.frequency),
            replace_existing=True
        )

    def one_time_scheduling(self):
        if not self.start_date:
            # when the job is scheduled to run immediately, it may happen that
            # the job is run even before the task is created, in which case
            # it fails because it cannot be retrieve from the Task column of
            # the database: we introduce a delta of 5 seconds.
            # other situation: the server is too slow and the job cannot be
            # run at all, eg 'job was missed by 0:00:09.465684'
            self.start_date = datetime.now() + timedelta(seconds=5)
        # execute the job immediately with a date-type job
        # when date is used as a trigger and run_date is left undetermined,
        # the job is executed immediately.
        scheduler.add_job(
            id=self.creation_time,
            run_date=self.start_date,
            func=job_multiprocessing,
            args=[self.name],
            trigger='date'
        )


def task_factory(**kwargs):
    task = get_obj(Task, name=kwargs['name'])
    if task:
        for property, value in kwargs.items():
            if property in ('start_date', 'end_date'):
                value = task.datetime_conversion(value)
            setattr(task, property, value)
    else:
        task = Task(**kwargs)
        db.session.add(task)
    db.session.commit()
