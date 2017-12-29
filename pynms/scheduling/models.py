from base.helpers import str_dict
from base.models import CustomBase
from datetime import datetime
from flask import current_app
from netmiko import ConnectHandler
from objects.models import get_obj
from sqlalchemy import Column, ForeignKey, Integer, String

# napalm pre and post-reunification compatibility
try:
    from napalm import get_network_driver
except ImportError:
    from napalm_base import get_network_driver

## Jobs

def netmiko_job(script, username, password, ips, driver, global_delay_factor):
    for ip_address in ips:
        netmiko_handler = ConnectHandler(                
            ip = ip_address,
            device_type = driver,
            username = username,
            password = password,
            global_delay_factor = global_delay_factor
            )
        netmiko_handler.send_config_set(script.splitlines())

def napalm_connection(ip_address, username, password, driver, optional_args):
    napalm_driver = get_network_driver(driver)
    connection = napalm_driver(
        hostname = ip_address, 
        username = username,
        password = password,
        optional_args = optional_args
        )
    connection.open()
    return connection

def napalm_config_job(script, username, password, nodes_info, action):
    for ip_address, driver in nodes_info:
        napalm_driver = napalm_connection(
            ip_address, 
            username,
            password,
            driver,
            {'secret': 'cisco'}
            )
        if action in ('load_merge_candidate', 'load_replace_candidate'):
            getattr(napalm_driver, action)(config=script)
        else:
            getattr(napalm_driver, action)()

def napalm_getters_job(getters, username, password, nodes_info):
    napalm_output = []
    for ip_address, driver in nodes_info:
        try:
            napalm_driver = napalm_connection(
                ip_address, 
                username,
                password,
                driver,
                {'secret': 'cisco'}
                )
            napalm_output.append('\n{}\n'.format(ip_address))
            for getter in getters:
                try:
                    output = str_dict(getattr(napalm_driver, getter)())
                    print(output)
                except Exception as e:
                    output = '{} could not be retrieve because of {}'.format(getter, e)
                    print(output)
                napalm_output.append(output)
        except Exception as e:
            output = 'could not be retrieve because of {}'.format(e)
            napalm_output.append(output)
            print(output)
    return napalm_output

## Tasks

class Task(CustomBase):
    
    __tablename__ = 'Task'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(120))
    creation_time = Column(Integer)
    
    # scheduling parameters
    frequency = Column(String(120))
    scheduled_date = Column(String)
    
    # script parameters
    creator = Column(String)
    
    def __init__(self, user, **data):
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
        id = current_app.scheduler.add_job(
            id = self.creation_time,
            func = self.job,
            args = self.args,
            trigger = 'interval',
            seconds = 5,
            replace_existing = True
            )

    def instant_scheduling(self):
        # execute the job immediately with a date-type job
        # when date is used as a trigger and run_date is left undetermined, 
        # the job is executed immediately.
        id = current_app.scheduler.add_job(
            id = self.creation_time,
            func = self.job,
            args = self.args,
            trigger = 'date',
            )

class NetmikoTask(Task):
    
    __tablename__ = 'NetmikoTask'
    
    id = Column(Integer, ForeignKey('Task.id'), primary_key=True)
    script = Column(String)
    
    def __init__(self, script, user, ips, **data):
        
        self.script = script
        self.user = user
        self.ips = ips
        self.data = data
        self.job = netmiko_job
        self.args = [
            self.script,
            self.user.username,
            self.user.password,
            self.ips,
            self.data['driver'],
            self.data['global_delay_factor'],
            ]
        super(NetmikoTask, self).__init__(user, **data)

class NapalmConfigTask(Task):
    
    __tablename__ = 'NapalmConfigTask'
    
    id = Column(Integer, ForeignKey('Task.id'), primary_key=True)
    script = Column(String)
    
    def __init__(self, script, user, nodes_info, **data):
        self.script = script
        self.user = user
        self.nodes_info = nodes_info
        self.data = data
        self.job = napalm_config_job
        self.args = [
            self.script,
            self.user.username,
            self.user.password,
            self.nodes_info,
            self.data['actions']
            ]
        super(NapalmConfigTask, self).__init__(user, **data)

class NapalmGettersTask(Task):
    
    __tablename__ = 'NapalmGettersTask'
    
    id = Column(Integer, ForeignKey('Task.id'), primary_key=True)
    script = Column(String)
    
    def __init__(self, user, nodes_info, **data):
        self.user = user
        self.nodes_info = nodes_info
        self.data = data
        self.job = napalm_getters_job
        self.args = [
            data['getters'],
            self.user.username,
            self.user.password,
            self.nodes_info
            ]
        super(NapalmGettersTask, self).__init__(user, **data)