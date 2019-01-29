from flask_login import UserMixin
from sqlalchemy import (
    Boolean,
    Column,
    Float,
    ForeignKey,
    Integer,
    PickleType,
    String
)
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.orm import relationship

from eNMS.main import db
from eNMS.base.models import Base


class User(Base, UserMixin):

    __tablename__ = type = 'User'
    id = Column(Integer, primary_key=True)
    email = Column(String)
    jobs = relationship('Job', back_populates='creator')
    name = Column(String, unique=True)
    permissions = Column(MutableList.as_mutable(PickleType), default=[])
    password = Column(String)

    @property
    def is_admin(self):
        return 'Admin' in self.permissions

    def allowed(self, permission):
        return self.is_admin or permission in self.permissions


class Instance(Base):

    __tablename__ = type = 'Instance'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    description = Column(String)
    ip_address = Column(String)
    weight = Column(Integer, default=1)
    status = Column(String, default='down')
    cpu_load = Column(Float)


class Parameters(Base):

    __tablename__ = type = 'Parameters'
    id = Column(Integer, primary_key=True)
    name = Column(String, default='default', unique=True)
    cluster_scan_subnet = Column(String)
    cluster_scan_protocol = Column(String)
    cluster_scan_timeout = Column(Float)
    default_longitude = Column(Float)
    default_latitude = Column(Float)
    default_zoom_level = Column(Integer)
    default_view = Column(String)
    git_repository_configurations = Column(String)
    git_repository_automation = Column(String)
    gotty_start_port = Column(Integer)
    gotty_end_port = Column(Integer)
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
    mail_sender = Column(String)
    mail_recipients = Column(String)
    mattermost_url = Column(String)
    mattermost_channel = Column(String)
    mattermost_verify_certificate = Column(Boolean)
    slack_token = Column(String)
    slack_channel = Column(String)
    pool_id = Column(Integer, ForeignKey('Pool.id'))
    pool = relationship('Pool')

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
