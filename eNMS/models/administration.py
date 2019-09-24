from flask_login import UserMixin
from sqlalchemy import Boolean, Float, Integer
from sqlalchemy.orm import relationship
from typing import Any, List

from eNMS.database.dialect import Column, MutableDict, MutableList, SmallString
from eNMS.database.associations import pool_user_table
from eNMS.database.base import AbstractBase


class Server(AbstractBase):

    __tablename__ = type = "server"
    id = Column(Integer, primary_key=True)
    name = Column(SmallString, unique=True)
    description = Column(SmallString)
    ip_address = Column(SmallString)
    weight = Column(Integer, default=1)
    status = Column(SmallString, default="down")
    cpu_load = Column(Float)

    def generate_row(self, table) -> List[str]:
        return [
            f"""<div class="btn-group" style="width: 80px;">
            <button type="button" class="btn btn-primary btn-sm"
            onclick="showTypePanel('server', '{self.id}')">Edit</button>,
            <button type="button" class="btn btn-primary btn-sm
            dropdown-toggle" data-toggle="dropdown">
              <span class="caret"></span>
            </button>
            <ul class="dropdown-menu" role="menu"><li><a href="#" onclick="
              showTypePanel('server', '{self.id}', 'duplicate')">Duplicate</a></li>
            </ul></div>""",
            f"""<button type="button" class="btn btn-danger btn-sm"
            onclick="showDeletionPanel({self.row_properties})">
            Delete</button>""",
        ]


class Parameters(AbstractBase):

    __tablename__ = type = "parameters"
    id = Column(Integer, primary_key=True)
    name = Column(SmallString, default="default", unique=True)
    cluster_scan_subnet = Column(SmallString)
    cluster_scan_protocol = Column(SmallString)
    cluster_scan_timeout = Column(Float)
    custom_config = Column(MutableDict)
    default_longitude = Column(Float)
    default_latitude = Column(Float)
    default_zoom_level = Column(Integer, default=0)
    default_view = Column(SmallString)
    default_marker = Column(SmallString)
    git_configurations = Column(SmallString)
    git_automation = Column(SmallString)
    gotty_start_port = Column(Integer, default=0)
    gotty_end_port = Column(Integer, default=0)
    gotty_port_index = Column(Integer, default=-1)
    opennms_rest_api = Column(
        SmallString, default="https://demo.opennms.org/opennms/rest"
    )
    opennms_devices = Column(
        SmallString, default="https://demo.opennms.org/opennms/rest/nodes"
    )
    opennms_login = Column(SmallString, default="demo")
    mail_sender = Column(SmallString)
    mail_recipients = Column(SmallString)
    mattermost_url = Column(SmallString)
    mattermost_channel = Column(SmallString)
    mattermost_verify_certificate = Column(Boolean, default=False)
    slack_token = Column(SmallString)
    slack_channel = Column(SmallString)

    def update(self, **kwargs):
        self.gotty_port_index = -1  # type: ignore
        super().update(**kwargs)


class User(AbstractBase, UserMixin):

    __tablename__ = type = "user"
    id = Column(Integer, primary_key=True)
    email = Column(SmallString)
    name = Column(SmallString)
    permissions = Column(MutableList)
    pools = relationship("Pool", secondary=pool_user_table, back_populates="users")
    password = Column(SmallString)

    def generate_row(self, table) -> List[str]:
        return [
            f"""<div class="btn-group">
            <button type="button" class="btn btn-primary btn-sm"
            onclick="showTypePanel('user', '{self.id}')">Edit</button>,
            <button type="button" class="btn btn-primary btn-sm
            dropdown-toggle" data-toggle="dropdown">
              <span class="caret"></span>
            </button>
            <ul class="dropdown-menu" role="menu"><li><a href="#" onclick="
            showTypePanel('user', '{self.id}', 'duplicate')">Duplicate</a></li>
            </ul></div>""",
            f"""<button type="button" class="btn btn-danger btn-sm"
            onclick="showDeletionPanel({self.row_properties})">
            Delete</button>""",
        ]

    @property
    def is_admin(self) -> bool:
        return "Admin" in self.permissions

    def allowed(self, permission) -> bool:
        return self.is_admin or permission in self.permissions
