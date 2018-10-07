from flask import current_app as app
from flask_login import UserMixin
from sqlalchemy import Column, Float, Integer, PickleType, String
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.orm import relationship
from passlib.hash import cisco_type7
try:
    from SocketServer import BaseRequestHandler, UDPServer
except Exception:
    from socketserver import BaseRequestHandler, UDPServer
from threading import Thread

from eNMS import db, scheduler
from eNMS.base.custom_base import CustomBase
from eNMS.base.helpers import vault_helper
from eNMS.base.models import Log


class User(CustomBase, UserMixin):

    __tablename__ = 'User'

    id = Column(Integer, primary_key=True)
    type = Column(String, default='admin')
    email = Column(String)
    name = Column(String, unique=True)
    permissions = Column(MutableList.as_mutable(PickleType), default=[])
    password = Column(String)
    tasks = relationship('Task', back_populates='user')

    def update(self, **kwargs):
        if app.production:
            data = {'password': kwargs.pop('password')}
            vault_helper(app, f'user/{kwargs["name"]}', data)
        super().update(**kwargs)

    @property
    def is_admin(self):
        return 'Admin' in self.permissions

    def allowed(self, permission):
        return self.is_admin or permission in self.permissions

    def __repr__(self):
        return self.name


class TacacsServer(CustomBase):

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


class SyslogUDPHandler(BaseRequestHandler):

    def handle(self):
        with scheduler.app.app_context():
            data = bytes.decode(self.request[0].strip())
            source, _ = self.client_address
            log = Log(source, str(data))
            db.session.add(log)
            db.session.commit()


class SyslogServer(CustomBase):

    __tablename__ = 'SyslogServer'

    id = Column(Integer, primary_key=True)
    ip_address = Column(String)
    port = Column(Integer)

    def __init__(self, **kwargs):
        self.ip_address = kwargs['ip_address']
        self.port = int(kwargs['port'])
        self.start()

    def __repr__(self):
        return self.ip_address

    def start(self):
        UDPServer.allow_reuse_address = True
        self.server = UDPServer((self.ip_address, self.port), SyslogUDPHandler)
        th = Thread(target=self.server.serve_forever)
        th.daemon = True
        th.start()


class Parameters(CustomBase):

    __tablename__ = 'Parameters'

    id = Column(Integer, primary_key=True)
    name = Column(String, default='default', unique=True)
    default_longitude = Column(Float, default=2.)
    default_latitude = Column(Float, default=48.)
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
