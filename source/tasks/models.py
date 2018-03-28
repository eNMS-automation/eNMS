from tempfile import NamedTemporaryFile
from base.database import db
from base.helpers import str_dict
from base.models import CustomBase
from collections import namedtuple
from datetime import datetime, timedelta
from flask_apscheduler import APScheduler
from multiprocessing.pool import ThreadPool
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

scheduler = APScheduler()

## Netmiko process and job


def netmiko_config_job(name, type, script_name, username, password, ips, driver,
                       global_delay_factor):
    job_time = str(datetime.now())
    task = db.session.query(Task)\
        .filter_by(name=name)\
        .first()
    script = db.session.query(ConfigScript)\
        .filter_by(name=script_name)\
        .first()
    pool = ThreadPool(processes=10)
    results = {}
    kwargs = [({
        'ip': ip_address,
        'device_type': driver,
        'username': username,
        'password': password,
        'secret': secret,
        'global_delay_factor': global_delay_factor,
        'name': device_name,
        'results': results,
        'type': type
    }) for device_name, ip_address, _, secret in ips]
    pool.map(script.job, kwargs)
    pool.close()
    pool.join()
    task.logs[job_time] = results
    db.session.commit()


def netmiko_file_transfer_job(name, type, script_name, username, password, ips,
                              driver, global_delay_factor):
    job_time = str(datetime.now())
    task = db.session.query(Task)\
        .filter_by(name=name)\
        .first()
    script = db.session.query(ConfigScript)\
        .filter_by(name=script_name)\
        .first()
    pool = ThreadPool(processes=10)
    results = {}
    kwargs = [({
        'ip': ip_address,
        'device_type': driver,
        'username': username,
        'password': password,
        'secret': secret,
        'global_delay_factor': global_delay_factor,
        'name': device_name,
        'results': results,
        'type': type
    }) for device_name, ip_address, _, secret in ips]
    pool.map(script.job, kwargs)
    pool.close()
    pool.join()
    task.logs[job_time] = results
    db.session.commit()

## Napalm processes and jobs


def napalm_config_job(name, script_name, username, password, nodes_info, action):
    job_time = str(datetime.now())
    task = db.session.query(Task)\
        .filter_by(name=name)\
        .first()
    script = db.session.query(ConfigScript)\
        .filter_by(name=script_name)\
        .first()
    pool = ThreadPool(processes=10)
    results = {}
    kwargs = [({
        'action': action,
        'ip_address': ip_address,
        'driver': driver,
        'username': username,
        'password': password,
        'secret': secret,
        'name': device_name,
        'script': script.content,
        'results': results
    }) for device_name, ip_address, driver, secret in nodes_info]
    pool.map(napalm_config_process, kwargs)
    pool.close()
    pool.join()
    task.logs[job_time] = results
    db.session.commit()


def napalm_getters_job(name, getters, username, password, nodes_info):
    job_time = str(datetime.now())
    task = db.session.query(Task)\
        .filter_by(name=name)\
        .first()
    pool = ThreadPool(processes=10)
    results = {}
    kwargs = [({
        'ip_address': ip_address,
        'driver': driver,
        'username': username,
        'password': password,
        'secret': secret,
        'name': device_name,
        'getters': getters,
        'results': results
    }) for device_name, ip_address, driver, secret in nodes_info]
    pool.map(napalm_getters_process, kwargs)
    pool.close()
    pool.join()
    task.logs[job_time] = results
    db.session.commit()


def ansible_job(name, script_name, username, password, nodes_info):
    job_time = str(datetime.now())
    task = db.session.query(Task)\
        .filter_by(name=name)\
        .first()
    script = db.session.query(AnsibleScript)\
        .filter_by(name=script_name)\
        .first()
    script.job(nodes_info)
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
    nodes = Column(MutableList.as_mutable(PickleType), default=[])

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

    def __init__(self, user, **data):
        self.name = data['name']
        self.frequency = data['frequency']
        self.recurrent = bool(data['frequency'])
        self.creation_time = str(datetime.now())
        self.creator = user.username
        self.status = 'active'
        # if the start date is left empty, we turn the empty string into
        # None as this is what AP Scheduler is expecting
        for date in ('start_date', 'end_date'):
            value = self.datetime_conversion(data[date]) if data[date] else None
            setattr(self, date, value)
        self.is_active = True
        if data['frequency']:
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
            func=self.job,
            args=self.args,
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
            func=self.job,
            args=self.args,
            trigger='date'
        )


class NetmikoConfigTask(Task):

    __tablename__ = 'NetmikoConfigTask'

    id = Column(Integer, ForeignKey('Task.id'), primary_key=True)
    script = Column(String)

    __mapper_args__ = {
        'polymorphic_identity': 'NetmikoConfigTask',
    }

    def __init__(self, user, targets, **data):
        self.subtype = data['type']
        self.script_name = data['script']
        self.user = user
        self.nodes = targets
        self.data = data
        self.job = netmiko_config_job
        self.args = [
            data['name'],
            data['type'],
            self.script_name,
            self.user.username,
            cisco_type7.decode(self.user.password),
            targets,
            data['driver'],
            data['global_delay_factor']
        ]
        super(NetmikoConfigTask, self).__init__(user, **data)


class NetmikoFileTransferTask(Task):

    __tablename__ = 'NetmikoFileTransferTask'

    id = Column(Integer, ForeignKey('Task.id'), primary_key=True)
    script = Column(String)

    __mapper_args__ = {
        'polymorphic_identity': 'NetmikoFileTransferTask',
    }

    def __init__(self, user, targets, **data):
        self.subtype = 'file_transfer'
        self.script_name = data['script']
        self.user = user
        self.nodes = targets
        self.data = data
        self.job = netmiko_file_transfer_job
        self.args = [
            data['name'],
            self.script_name,
            self.user.username,
            cisco_type7.decode(self.user.password),
            targets,
            data['driver'],
            data['global_delay_factor']
        ]
        super(NetmikoFileTransferTask, self).__init__(user, **data)


class NapalmConfigTask(Task):

    __tablename__ = 'NapalmConfigTask'

    id = Column(Integer, ForeignKey('Task.id'), primary_key=True)
    script = Column(String)

    __mapper_args__ = {
        'polymorphic_identity': 'NapalmConfigTask',
    }

    def __init__(self, user, targets, **data):
        self.subtype = 'napalm_config'
        self.script_name = data['script']
        self.user = user
        self.nodes = targets
        self.data = data
        self.job = napalm_config_job
        self.args = [
            data['name'],
            self.script_name,
            self.user.username,
            cisco_type7.decode(self.user.password),
            targets,
            data['actions']
        ]
        super(NapalmConfigTask, self).__init__(user, **data)


class NapalmGettersTask(Task):

    __tablename__ = 'NapalmGettersTask'

    id = Column(Integer, ForeignKey('Task.id'), primary_key=True)
    script = Column(String)

    __mapper_args__ = {
        'polymorphic_identity': 'NapalmGettersTask',
    }

    def __init__(self, user, targets, **data):
        self.subtype = 'napalm_getters'
        self.user = user
        self.nodes = targets
        self.data = data
        self.job = napalm_getters_job
        self.args = [
            data['name'],
            data['getters'],
            self.user.username,
            cisco_type7.decode(self.user.password),
            targets
        ]
        super(NapalmGettersTask, self).__init__(user, **data)


class AnsibleTask(Task):

    __tablename__ = 'AnsibleTask'

    id = Column(Integer, ForeignKey('Task.id'), primary_key=True)
    script = Column(String)

    __mapper_args__ = {
        'polymorphic_identity': 'AnsibleTask',
    }

    def __init__(self, user, targets, **data):
        self.subtype = 'ansible'
        self.script_name = data['script']
        self.user = user
        self.nodes = targets
        self.data = data
        self.job = ansible_job
        self.args = [
            data['name'],
            self.script_name,
            self.user.username,
            cisco_type7.decode(self.user.password),
            targets
        ]
        super(AnsibleTask, self).__init__(user, **data)
