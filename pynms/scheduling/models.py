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
        print(ip_address, driver, username, password, global_delay_factor)
        netmiko_handler = ConnectHandler(                
            ip = ip_address,
            device_type = driver,
            username = username,
            password = password,
            global_delay_factor = global_delay_factor
            )
        netmiko_handler.send_config_set(script.splitlines())

def napalm_job(script, username, password, nodes_info, action):
    napalm_output = []
    # print('napalm'*1000)
    for ip_address, driver in nodes_info:
        try:
            driver = get_network_driver(driver)
            napalm_driver = driver(
                hostname = ip_address, 
                username = username,
                password = password,
                optional_args = {'secret': 'cisco'}
                )
            napalm_driver.open()
            if action in ('load_merge_candidate', 'load_replace_candidate'):
                getattr(napalm_driver, action)(config=script)
            else:
                getattr(napalm_driver, action)()
        except Exception as e:
            output = 'exception {}'.format(e)
            napalm_output.append(output)
            print(e)
    return '\n\n'.join(napalm_output)

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

    def datetime_conversion(self, scheduled_date):
        dt = datetime.strptime(scheduled_date, '%d/%m/%Y %H:%M:%S')
        return datetime.strftime(dt, '%Y-%m-%d %H:%M:%S')
                
    def pause_task(self):
        scheduler.pause_job(self.name)
        self.status = 'Suspended'
        
    def resume_task(self):
        scheduler.resume_job(self.name)
        self.status = "Active"

class NetmikoTask(Task):
    
    __tablename__ = 'NetmikoTask'
    
    id = Column(Integer, ForeignKey('Task.id'), primary_key=True)
    script = Column(String)
    
    def __init__(self, script, user, ips, **data):
        super(NetmikoTask, self).__init__(user, **data)
        self.script = script
        self.user = user
        self.ips = ips
        self.data = data
        if not data['scheduled_date']:
            self.instant_scheduling()

    def instant_scheduling(self):
        # execute the job immediately: 1-second interval job
        id = current_app.scheduler.add_job(
            id = self.creation_time,
            func = netmiko_job,
            args = [
                self.script,
                self.user.username,
                self.user.password,
                self.ips,
                self.data['driver'],
                self.data['global_delay_factor'],
                ],
            trigger = 'interval',
            seconds = 5,
            replace_existing = True
            )

class NapalmConfigTask(Task):
    
    __tablename__ = 'NapalmTask'
    
    id = Column(Integer, ForeignKey('Task.id'), primary_key=True)
    script = Column(String)
    
    def __init__(self, script, user, nodes_info, **data):
        super(NapalmConfigTask, self).__init__(user, **data)
        self.script = script
        self.user = user
        self.nodes_info = nodes_info
        self.data = data
        if not data['scheduled_date']:
            self.instant_scheduling()

    def instant_scheduling(self):
        # execute the job immediately: 1-second interval job
        id = current_app.scheduler.add_job(
            id = self.creation_time,
            func = napalm_job,
            args = [
                self.script,
                self.user.username,
                self.user.password,
                self.nodes_info,
                self.data['actions']
                ],
            trigger = 'interval',
            seconds = 5,
            replace_existing = True
            )