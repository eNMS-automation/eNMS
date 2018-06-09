from flask_login import UserMixin
from sqlalchemy import Column, Float, Integer, String
from sqlalchemy.orm import relationship
from passlib.hash import cisco_type7
try:
    from SocketServer import BaseRequestHandler, UDPServer
except Exception:
    from socketserver import BaseRequestHandler, UDPServer
from threading import Thread


from eNMS import db
from eNMS.base.models import CustomBase, get_obj
from eNMS.base.helpers import integrity_rollback
from eNMS.base.models import Log


class User(CustomBase, UserMixin):

    __tablename__ = 'User'

    id = Column(Integer, primary_key=True)
    type = Column(String, default='admin')
    name = Column(String(120), unique=True)
    email = Column(String(120), unique=True)
    access_rights = Column(String(120))
    password = Column(String(30))
    secret_password = Column(String(30))
    tasks = relationship('Task', back_populates='user')

    def __init__(self, **kwargs):
        password = kwargs.pop('password')
        kwargs['password'] = cisco_type7.hash(password)
        for property, value in kwargs.items():
            # depending on whether value is an iterable or not, we must
            # unpack it's value (when **kwargs is request.form, some values
            # will be a 1-element list)
            if hasattr(value, '__iter__') and not isinstance(value, str):
                value = value[0]
            setattr(self, property, value)

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


def user_factory(**kwargs):
    user = get_obj(User, name=kwargs['name'])
    if user:
        for property, value in kwargs.items():
            if property in user.__dict__:
                if property == 'password':
                    value = cisco_type7.hash(value)
                setattr(user, property, value)
    else:
        user = User(**kwargs)
        db.session.add(user)
    db.session.commit()
    return user


class SyslogUDPHandler(BaseRequestHandler):

    def handle(self):
        data = bytes.decode(self.request[0].strip())
        source, _ = self.client_address
        log = Log(source, str(data))
        db.session.add(log)
        db.session.commit()


class SyslogServer(CustomBase):

    __tablename__ = 'SyslogServer'

    id = Column(Integer, primary_key=True)
    ip_address = Column(String(120))
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

    def update(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


@integrity_rollback
def create_default_parameters():
    parameters = Parameters()
    db.session.add(parameters)
    db.session.commit()
