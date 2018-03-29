from flask_login import UserMixin
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from base.models import CustomBase
from passlib.hash import cisco_type7


class User(CustomBase, UserMixin):

    __tablename__ = 'User'

    id = Column(Integer, primary_key=True)
    username = Column(String(120), unique=True)
    email = Column(String(120), unique=True)
    access_rights = Column(String(120))
    password = Column(String(30))
    secret_password = Column(String(30))
    task_id = Column(Integer, ForeignKey('Task.id'))
    tasks = relationship("Task")
    dashboard_node_properties = Column(String())
    dashboard_link_properties = Column(String())

    def __init__(self, **kwargs):
        for property, value in kwargs.items():
            # depending on whether value is an iterable or not, we must
            # unpack it's value (when **kwargs is request.form, some values
            # will be a 1-element list)
            if hasattr(value, '__iter__') and not isinstance(value, str):
                value = value[0]
            setattr(self, property, value)
        self.dashboard_node_properties = str(['type'])
        self.dashboard_link_properties = str(['type'])

    def __repr__(self):
        return self.username


class TacacsServer(CustomBase):

    __tablename__ = 'TacacsServer'

    id = Column(Integer, primary_key=True)
    ip_address = Column(String(120), unique=True)
    password = Column(String(120), unique=True)
    port = Column(Integer)

    def __init__(self, **kwargs):
        self.ip_address = str(kwargs['ip_address'][0])
        self.password = str(cisco_type7.hash(''.join(kwargs['password'])))
        self.port = int(''.join(kwargs['port']))

    def __repr__(self):
        return self.ip_address
