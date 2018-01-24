from base.database import db
from base.helpers import str_dict
from base.models import CustomBase
from collections import defaultdict
from datetime import datetime, timedelta
from flask import current_app
from flask_apscheduler import APScheduler
from multiprocessing.pool import ThreadPool
from netmiko import ConnectHandler
from passlib.hash import cisco_type7
from scripts.models import *
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, PickleType
from sqlalchemy.ext.mutable import MutableDict, MutableList

# napalm pre and post-reunification compatibility
try:
    from napalm import get_network_driver
except ImportError:
    from napalm_base import get_network_driver

scheduler = APScheduler()
scheduler.start()

## Netmiko process and job

def netmiko_process(kwargs):
    results = kwargs.pop('results')
    script, name = kwargs.pop('script'), kwargs.pop('name')
    script_type = kwargs.pop('type')
    try:
        netmiko_handler = ConnectHandler(**kwargs)
        if script_type == 'configuration':
            netmiko_handler.send_config_set(script.splitlines())
            result = 'configuration OK'
        else:
            outputs = []
            for show_command in script.splitlines():
                outputs.append(netmiko_handler.send_command(show_command))
            result = '\n\n'.join(outputs)
    except Exception as e:
        result = 'netmiko config did not work because of {}'.format(e)
    results[name] = result
    netmiko_handler.disconnect()

def netmiko_job(name, type, script_name, username, password, ips, 
                    driver, global_delay_factor):
    job_time = str(datetime.now())
    task = db.session.query(Task)\
        .filter_by(name=name)\
        .first()
    script = db.session.query(ClassicScript)\
        .filter_by(name=script_name)\
        .first() 
    pool = ThreadPool(processes=100)
    results = {}
    kwargs = [({
        'ip': ip_address,
        'device_type': driver,
        'username': username,
        'password': password,
        'secret': secret,
        'global_delay_factor': global_delay_factor,
        'name': device_name,
        'script': script.content,
        'results': results,
        'type': type
        }) for device_name, ip_address, _, secret in ips]
    pool.map(netmiko_process, kwargs)
    task.logs[job_time] = results
    db.session.commit()

## Napalm processes and jobs

def napalm_config_process(kwargs):
    try:
        driver = get_network_driver(kwargs['driver'])
        napalm_driver = driver(
            hostname = kwargs['ip_address'], 
            username = kwargs['username'],
            password = kwargs['password'],
            optional_args = {'secret': kwargs['secret']}
            )
        napalm_driver.open()
        if kwargs['action'] in ('load_merge_candidate', 'load_replace_candidate'):
            getattr(napalm_driver, kwargs['action'])(config=kwargs['script'])
        else:
            getattr(napalm_driver, kwargs['action'])()
        napalm_driver.close()
    except Exception as e:
        result = 'napalm config did not work because of {}'.format(e)
    else:
        result = 'configuration OK'
    kwargs['results'][kwargs['name']] = result

def napalm_config_job(name, script_name, username, password, nodes_info, action):
    job_time = str(datetime.now())
    task = db.session.query(Task)\
        .filter_by(name=name)\
        .first()
    script = db.session.query(ClassicScript)\
        .filter_by(name=script_name)\
        .first()
    pool = ThreadPool(processes=100)
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
    task.logs[job_time] = results
    db.session.commit()

def napalm_getters_process(kwargs):
    try:
        driver = get_network_driver(kwargs['driver'])
        napalm_driver = driver(
            hostname = kwargs['ip_address'], 
            username = kwargs['username'],
            password = kwargs['password'],
            optional_args = {'secret': kwargs['secret']}
            )
        napalm_driver.open()
        for getter in kwargs['getters']:
            try:
                result = str_dict(getattr(napalm_driver, getter)())
            except Exception as e:
                result = '{} could not be retrieve because of {}'.format(getter, e)
        napalm_driver.close()
    except Exception as e:
        result = 'getters process did not work because of {}'.format(e)
    kwargs['results'][kwargs['name']] = result

def napalm_getters_job(name, getters, username, password, nodes_info):
    job_time = str(datetime.now())
    task = db.session.query(Task)\
        .filter_by(name=name)\
        .first()
    pool = ThreadPool(processes=100)
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
    scheduled_date = Column(String)
    
    # script parameters
    creator = Column(String)
    
    def __init__(self, user, **data):
        self.name = data['name']
        self.frequency = data['frequency']
        self.recurrent = bool(data['frequency'])
        self.creation_time = str(datetime.now())
        self.creator = user.username
        self.status = 'active'
        # if the scheduled date is left empty, we turn the empty string into
        # None as this is what AP Scheduler is expecting
        if data['scheduled_date']:
            self.scheduled_date = self.datetime_conversion(data['scheduled_date'])
        else:
            self.scheduled_date = None
        self.is_active = True
        if data['frequency']:
            self.recurrent_scheduling()
        else:
            self.one_time_scheduling()

    def datetime_conversion(self, scheduled_date):
        dt = datetime.strptime(scheduled_date, '%d/%m/%Y %H:%M:%S')
        return datetime.strftime(dt, '%Y-%m-%d %H:%M:%S')
                
    def pause_task(self):
        scheduler.pause_job(self.creation_time)
        self.status = 'suspended'
        db.session.commit()
        
    def resume_task(self):
        scheduler.resume_job(self.creation_time)
        self.status = "active"
        db.session.commit()

    def recurrent_scheduling(self):
        if not self.scheduled_date:
            self.scheduled_date = datetime.now() + timedelta(seconds=15)
        # run the job on a regular basis with an interval trigger
        id = scheduler.add_job(
            id = self.creation_time,
            func = self.job,
            args = self.args,
            trigger = 'interval',
            start_date = self.scheduled_date,
            seconds = int(self.frequency),
            replace_existing = True
            )

    def one_time_scheduling(self):
        if not self.scheduled_date:
            # when the job is scheduled to run immediately, it may happen that
            # the job is run even before the task is created, in which case
            # it fails because it cannot be retrieve from the Task column of 
            # the database: we introduce a delta of 2 seconds.
            # other situation: the server is too slow and the job cannot be
            # run at all, eg 'job was missed by 0:00:09.465684'
            self.scheduled_date = datetime.now() + timedelta(seconds=5)
        # execute the job immediately with a date-type job
        # when date is used as a trigger and run_date is left undetermined, 
        # the job is executed immediately.
        id = scheduler.add_job(
            id = self.creation_time,
            run_date = self.scheduled_date,
            func = self.job,
            args = self.args,
            trigger = 'date'
            )

class NetmikoTask(Task):
    
    __tablename__ = 'NetmikoTask'
    
    id = Column(Integer, ForeignKey('Task.id'), primary_key=True)
    script = Column(String)
    
    def __init__(self, user, targets, **data):
        print(user, targets, data)
        self.type = data['type']
        self.script_name = data['script']
        self.user = user
        self.nodes = targets
        self.data = data
        self.job = netmiko_job
        self.args = [
            data['name'],
            data['type'],
            self.script_name,
            self.user.username,
            cisco_type7.decode(self.user.password),
            targets,
            data['driver'],
            data['global_delay_factor'],
            ]
        super(NetmikoTask, self).__init__(user, **data)

class NapalmConfigTask(Task):
    
    __tablename__ = 'NapalmConfigTask'
    
    id = Column(Integer, ForeignKey('Task.id'), primary_key=True)
    script = Column(String)
    
    def __init__(self, user, targets, **data):
        self.type = 'napalm_config'
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
    
    def __init__(self, user, targets, **data):
        self.type = 'napalm_getters'
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