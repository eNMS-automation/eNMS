from datetime import datetime
from napalm import get_network_driver
from netmiko import ConnectHandler
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, ForeignKey
from app import db, scheduler
from database import Base

class CustomBase(Base):
    
    __abstract__ = True
    
    def __init__(self, **kwargs):
        for property, value in kwargs.items():
            if property in self.__table__.columns._data:
                # depending on whether value is an iterable or not, we must
                # unpack it's value (when **kwargs is request.form, some values
                # will be a 1-element list)
                if hasattr(value, '__iter__') and not isinstance(value, str):
                    value ,= value
                setattr(self, property, value)

class User(CustomBase):
    
    __tablename__ = 'User'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True)
    access_rights = db.Column(db.String(120))
    password = db.Column(db.String(30))
    secret_password = db.Column(db.String(30))
        
    def __repr__(self):
        return str(self.username)
        
class Task(Base):
    
    __tablename__ = 'Task'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True)
    creation_time = db.Column(db.Integer)
    
    # scheduling parameters
    frequency = db.Column(db.String(120))
    scheduled_date = db.Column(db.String)
    
    # script parameters
    script = db.Column(db.String)
    creator = db.Column(db.String)
    
    def __init__(self, script, **data):
        self.name = data['name']
        self.frequency = data['frequency']
        self.scheduled_date = data['scheduled_date']
        self.creation_time = str(datetime.now())
        self.creator = data['user']
        self.script = script
        # by default, a task is active but it can be deactivated
        self.is_active = True
        
    def __repr__(self):
        return str(self.name)


class Device(CustomBase):
    
    __tablename__ = 'Device'

    id = db.Column(db.Integer, primary_key=True)
    hostname = db.Column(db.String(120))
    ip_address = db.Column(db.String(120))
    vendor = db.Column(db.String(120))
    operating_system = db.Column(db.String(120))
    os_version = db.Column(db.String(120))
    longitude = db.Column(db.Float)
    latitude = db.Column(db.Float)
        
    def napalm_connection(self, user, driver, transport):
        driver = get_network_driver(driver)
        device = driver(
                        hostname = self.ip_address, 
                        username = user.username,
                        password = user.password, 
                        optional_args = {
                                         'secret': user.secret, 
                                         'transport': transport
                                         }
                        )
        device.open()
        return device
        
    def netmiko_scheduler(self, script, **data):
        # execute the job immediately: 1-second interval job
        scheduler.add_job(
                        id = ''.join(selected_devices) + scheduler_interval,
                        func = netmiko_job,
                        args = [                            
                                script,
                                data['username'],
                                data['driver'],
                                data['global_delay_factor']
                                ],
                        trigger = 'interval',
                        seconds = 1,
                        replace_existing = True
                        )
                
    def netmiko_job(self, script, username, driver, global_delay_factor):
        user = db.session.query(User).filter_by(username=username).first()
        netmiko_handler = ConnectHandler(                
                                        host = self.hostname,
                                        device_type = driver,
                                        username = user.username,
                                        password = user.password,
                                        secret = user.secret,
                                        global_delay_factor = global_delay_factor
                                        )
        netmiko_handler.send_config_set(script.splitlines())
        
    def __repr__(self):
        return self.hostname
        
class Link(CustomBase):
    
    __tablename__ = 'Link'

    source_id = Column(
                       Integer,
                       ForeignKey('Device.id'),
                       primary_key=True
                       )

    destination_id = Column(
                            Integer,
                            ForeignKey('Device.id'),
                            primary_key=True
                            )
        
    source = relationship(
                         Device,
                         primaryjoin = source_id == Device.id,
                         backref = 'sources'
                         )

    destination = relationship(
                               Device,
                               primaryjoin = destination_id == Device.id,
                               backref = 'destinations'
                               )
