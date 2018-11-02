from flask import current_app as app
from flask_login import UserMixin
from sqlalchemy import Column, Float, Integer, PickleType, String
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.orm import relationship
from passlib.hash import cisco_type7

from eNMS import db
from eNMS.base.models import Base
from eNMS.base.security import vault_helper


class User(Base, UserMixin):

    __tablename__ = 'User'

    id = Column(Integer, primary_key=True)
    type = Column(String, default='admin')
    email = Column(String)
    name = Column(String, unique=True)
    permissions = Column(MutableList.as_mutable(PickleType), default=[])
    password = Column(String)
    tasks = relationship('Task', back_populates='user')

    def update(self, **kwargs):
        if app.config['USE_VAULT']:
            data = {'password': kwargs.pop('password')}
            vault_helper(app, f'user/{kwargs["name"]}', data)
        super().update(**kwargs)

    @property
    def is_admin(self):
        return 'Admin' in self.permissions

    def allowed(self, permission):
        return self.is_admin or permission in self.permissions


class TacacsServer(Base):

    __tablename__ = 'TacacsServer'

    id = Column(Integer, primary_key=True)
    ip_address = Column(String(120))
    password = Column(String(120))
    port = Column(Integer)
    timeout = Column(Integer)

    def __init__(self, **kwargs):
        self.ip_address = kwargs['ip_address']
        self.password = cisco_type7.hash(kwargs['password'])
        self.port = int(kwargs['port'])
        self.timeout = int(kwargs['timeout'])

    def __repr__(self):
        return self.ip_address


class Parameters(Base):

    __tablename__ = 'Parameters'

    id = Column(Integer, primary_key=True)
    name = Column(String, default='default', unique=True)
    default_longitude = Column(Float, default=-96.)
    default_latitude = Column(Float, default=33.)
    default_zoom_level = Column(Integer, default=5)
    gotty_start_port = Column(Integer, default=9000)
    gotty_end_port = Column(Integer, default=9100)
    gotty_port_index = Column(Integer, default=-1)
    opennms_rest_api = Column(
        String,
        default='https://demo.opennms.org/opennms/rest'
    )
    opennms_devices = Column(
        String,
        default='https://demo.opennms.org/opennms/rest/nodes'
    )
    opennms_login = Column(String, default='demo')
    mail_sender = Column(String, default='enms@enms.fr')
    mail_recipients = Column(String)
    mattermost_url = Column(
        String,
        default='http://192.168.105.2:8065/hooks/dnuajekqp78jjbbajo8ewuw4ih'
    )
    mattermost_channel = Column(String)

    def update(self, **kwargs):
        self.gotty_port_index = -1
        super().update(**kwargs)

    @property
    def gotty_range(self):
        return self.gotty_end_port - self.gotty_start_port

    def get_gotty_port(self):
        self.gotty_port_index += 1
        db.session.commit()
        return self.gotty_start_port + self.gotty_port_index % self.gotty_range
