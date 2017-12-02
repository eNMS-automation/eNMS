from napalm import get_network_driver
from netmiko import ConnectHandler
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, ForeignKey
from app import db
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
        
    def napalm_connection(self, username, password, secret, transport):
        driver = get_network_driver(self.operating_system)
        device = driver(
                        hostname = self.ip_address, 
                        username = username,
                        password = password, 
                        optional_args = {
                                         'secret': secret, 
                                         'transport': transport
                                         }
                        )
        device.open()
        return device
        
    def netmiko_connection(self, device, user, netmiko_form):
        return ConnectHandler(                
                host = device,
                device_type = netmiko_form.data['driver'],
                username = user.username,
                password = user.password,
                secret = user.secret,
                global_delay_factor = netmiko_form.data['global_delay_factor']
                )
        
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
