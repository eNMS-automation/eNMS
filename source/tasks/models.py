from tempfile import NamedTemporaryFile
from base.database import db
from base.helpers import str_dict
from base.models import association_table, CustomBase
from collections import namedtuple
from datetime import datetime, timedelta
from flask_apscheduler import APScheduler
from multiprocessing.pool import ThreadPool
from objects.models import get_obj
from passlib.hash import cisco_type7
from scripts.models import (
    AnsibleScript,
    FileTransferScript,
    NapalmConfigScript,
    NapalmGettersScript,
    NetmikoConfigScript
)
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, PickleType
from sqlalchemy.ext.mutable import MutableDict, MutableList
from sqlalchemy.orm import relationship

scheduler = APScheduler()

## Netmiko process and job


def job_multiprocessing(name):
    job_time = str(datetime.now())
    task = get_obj(db, Task, name=name)
    print(task.__dict__)
    print(task.user)
    print(task.user.__dict__)
    print(task.script)
    print(task.script.__dict__)
    # pool = ThreadPool(processes=10)
    # results = {}
    # kwargs = [({
    #     'ip': ip_address,
    #     'device_type': driver,
    #     'username': username,
    #     'password': password,
    #     'secret': secret,
    #     'global_delay_factor': global_delay_factor,
    #     'name': device_name,
    #     'results': results,
    #     'type': type
    # }) for device_name, ip_address, _, secret in ips]
    # pool.map(script.job, kwargs)
    # pool.close()
    # pool.join()
    task.logs[job_time] = results
    db.session.commit()


## Tasks


class Task(CustomBase):

    __tablename__ = 'Task'

    id = Column(Integer, primary_key=True)
    type = Column(String)
    recurrent = Column(Boolean, default=False)
    name = Column(String(120), unique=True)
    status = Column(String)
    creation_time = Column(Integer)
    logs = Column(MutableDict.as_mutable(PickleType), default={})
    nodes = relationship(
        "Node",
        secondary=association_table,
        back_populates="tasks"
    )
    job = relationship('Job', back_populates='tasks', uselist=False)
    user = relationship('User', back_populates='tasks', uselist=False)

    # scheduling parameters
    frequency = Column(String(120))
    start_date = Column(String)
    end_date = Column(String)

    # script parameters
    creator = Column(String)

    __mapper_args__ = {
        'polymorphic_identity': 'Task',
        'polymorphic_on': type
    }

    def __init__(self, **data):
        self.data = data
        self.name ,= data['name']
        print(data)
        self.nodes = data['nodes']
        self.user = data['user']
        self.frequency ,= data['frequency']
        self.recurrent = bool(self.frequency)
        self.creation_time = str(datetime.now())
        self.creator = data['user'].username
        self.status = 'active'
        # if the start date is left empty, we turn the empty string into
        # None as this is what AP Scheduler is expecting
        for date in ('start_date', 'end_date'):
            date ,= data[date]
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
