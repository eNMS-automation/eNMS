from base.database import db
from base.helpers import str_dict
from base.models import CustomBase
from collections import defaultdict
from datetime import datetime, timedelta
from flask import current_app
from flask_apscheduler import APScheduler
from automation.models import Script
from netmiko import ConnectHandler
from objects.models import get_obj
from sqlalchemy import Column, ForeignKey, Integer, String, PickleType
from sqlalchemy.ext.mutable import MutableDict, MutableList

# napalm pre and post-reunification compatibility
try:
    from napalm import get_network_driver
except ImportError:
    from napalm_base import get_network_driver

scheduler = APScheduler()
scheduler.start()

## Jobs

def netmiko_job(name, script_name, username, password, ips, driver, global_delay_factor):
    job_time = str(datetime.now())
    task = db.session.query(Task)\
        .filter_by(name=name)\
        .first()
    script = db.session.query(Script)\
        .filter_by(name=script_name)\
        .first()
    task.logs[job_time] = {}
    for name, ip_address, _ in ips:
        try:
            netmiko_handler = ConnectHandler(                
                ip = ip_address,
                device_type = driver,
                username = username,
                password = password,
                global_delay_factor = global_delay_factor
                )
            netmiko_handler.send_config_set(script.content.splitlines())
        except Exception as e:
            result = 'netmiko config did not work because of {}'.format(e)
        else:
            result = 'configuration OK'
        task.logs[job_time][name] = result
    db.session.commit()

def napalm_connection(ip_address, username, password, driver, optional_args):
    napalm_driver = get_network_driver(driver)
    connection = napalm_driver(
        hostname = ip_address, 
        username = username,
        password = password,
        optional_args = {'secret': 'cisco'}
        )
    connection.open()
    return connection

def napalm_config_job(name, script_name, username, password, nodes_info, action):
    job_time = str(datetime.now())
    task = db.session.query(Task)\
        .filter_by(name=name)\
        .first()
    script = db.session.query(Script)\
        .filter_by(name=script_name)\
        .first()
    task.logs[job_time] = {}
    for name, ip_address, driver in nodes_info:
        try:
            napalm_driver = napalm_connection(
                ip_address, 
                username,
                password,
                driver,
                {'secret': 'cisco'}
                )
            if action in ('load_merge_candidate', 'load_replace_candidate'):
                getattr(napalm_driver, action)(config=script.content)
                napalm_driver.commit_config()
            else:
                getattr(napalm_driver, action)()
        except Exception as e:
            result = 'netmiko config did not work because of {}'.format(e)
        else:
            result = 'configuration OK'
        task.logs[job_time][name] = result
    db.session.commit()

def napalm_getters_job(name, getters, username, password, nodes_info):
    job_time = str(datetime.now())
    task = db.session.query(Task)\
        .filter_by(name=name)\
        .first()
    task.logs[job_time] = {}
    for name, ip_address, driver in nodes_info:
        try:
            napalm_driver = napalm_connection(
                ip_address, 
                username,
                password,
                driver,
                {'secret': 'cisco'}
                )
            for getter in getters:
                try:
                    result = str_dict(getattr(napalm_driver, getter)())
                except Exception as e:
                    result = '{} could not be retrieve because of {}'.format(getter, e)
        except Exception as e:
            result = 'could not be retrieve because of {}'.format(e)
        task.logs[job_time][name] = result
    db.session.commit()


## Tasks

class Task(CustomBase):
    
    __tablename__ = 'Task'
    
    id = Column(Integer, primary_key=True)
    type = Column(String)
    name = Column(String(120), unique=True)
    creation_time = Column(Integer)
    logs = Column(MutableDict.as_mutable(PickleType), default={})
    nodes = Column(MutableList.as_mutable(PickleType), default=[])
    
    # scheduling parameters
    frequency = Column(String(120))
    scheduled_date = Column(String)
    
    # script parameters
    creator = Column(String)
    
    def __init__(self, user, **data):
        print('s'*1000, data['name'])
        self.name = data['name']
        self.frequency = data['frequency']
        self.creation_time = str(datetime.now())
        self.creator = user.username
        # by default, a task is active but it can be pause
        self.is_active = True
        if data['scheduled_date']:
            self.scheduled_date = self.datetime_conversion(data['scheduled_date'])
            self.recurrent_scheduling()
        else:
            self.instant_scheduling()

    def datetime_conversion(self, scheduled_date):
        dt = datetime.strptime(scheduled_date, '%d/%m/%Y %H:%M:%S')
        return datetime.strftime(dt, '%Y-%m-%d %H:%M:%S')
                
    def pause_task(self):
        scheduler.pause_job(self.name)
        self.status = 'Suspended'
        
    def resume_task(self):
        scheduler.resume_job(self.name)
        self.status = "Active"

    def recurrent_scheduling(self):
        # run the job on a regular basis with an interval trigger
        id = scheduler.add_job(
            id = self.name,
            func = self.job,
            args = self.args,
            trigger = 'interval',
            seconds = 40,
            replace_existing = True
            )

    def instant_scheduling(self):
        # execute the job immediately with a date-type job
        # when date is used as a trigger and run_date is left undetermined, 
        # the job is executed immediately.
        id = scheduler.add_job(
            id = self.name,
            # when the job is scheduled to run immediately, it may happen that
            # the job is run even before the task is created, in which case
            # it fails because it cannot be retrieve from the Task column of 
            # the database: we introduce a delta of 2 seconds.
            # other situation: the server is too slow and the job cannot be
            # run at all: 'job was missed by 0:00:09.465684'
            run_date = datetime.now() + timedelta(seconds=2),
            func = self.job,
            args = self.args,
            trigger = 'date',
            )

class NetmikoTask(Task):
    
    __tablename__ = 'NetmikoTask'
    
    id = Column(Integer, ForeignKey('Task.id'), primary_key=True)
    script = Column(String)
    
    def __init__(self, user, targets, **data):
        self.type = 'netmiko'
        self.script_name = data['script']
        self.user = user
        self.nodes = targets
        self.data = data
        self.job = netmiko_job
        print('t'*1000, data['name'])
        self.args = [
            data['name'],
            self.script_name,
            self.user.username,
            self.user.password,
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
            self.user.password,
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
            self.user.password,
            targets
            ]
        super(NapalmGettersTask, self).__init__(user, **data)