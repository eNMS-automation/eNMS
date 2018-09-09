from bcrypt import gensalt, hashpw
from flask import current_app
from flask_login import UserMixin
from sqlalchemy import Column, Float, Integer, String
from sqlalchemy.orm import relationship
from passlib.hash import cisco_type7
try:
    from SocketServer import BaseRequestHandler, UDPServer
except Exception:
    from socketserver import BaseRequestHandler, UDPServer
from threading import Thread

from eNMS import db, scheduler
from eNMS.base.custom_base import CustomBase
from eNMS.base.models import Log


class User(CustomBase, UserMixin):

    __tablename__ = 'User'

    id = Column(Integer, primary_key=True)
    type = Column(String, default='admin')
    name = Column(String(120), unique=True)
    email = Column(String(120), unique=True)
    access_rights = Column(String(120))
    password = Column(String(30))
    tasks = relationship('Task', back_populates='user')

    def update(self, **kwargs):
        hash = hashpw(kwargs.pop('password').encode('utf8'), gensalt())
        if current_app.production:
            current_app.vault_client.write(
                f'secret/data/user/{kwargs["name"]}',
                data={'password': hash}
            )
        else:
            kwargs['password'] = hash
        super().update(**kwargs)

    def __repr__(self):
        return self.name


class TacacsServer(CustomBase):

    __tablename__ = 'TacacsServer'

    id = Column(Integer, primary_key=True)
    ip_address = Column(String(120), unique=True)
    password = Column(String(120), unique=True)
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
    ip_address = Column(String, unique=True)
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


class OpenNmsServer(CustomBase):

    __tablename__ = 'OpenNmsServer'

    id = Column(Integer, primary_key=True)
    rest_query = Column(String)
    device_query = Column(String)
    type = Column(String)
    login = Column(String)
    password = Column(String)


class Parameters(CustomBase):

    __tablename__ = 'Parameters'

    id = Column(Integer, primary_key=True)
    name = Column(String, default='default', unique=True)
    default_longitude = Column(Float, default=2.)
    default_latitude = Column(Float, default=48.)
    default_zoom_level = Column(Integer, default=5)
