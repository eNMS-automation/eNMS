from flask_login import UserMixin
from sqlalchemy import Boolean, Column, Float, Integer, PickleType, String
from sqlalchemy.ext.mutable import MutableDict, MutableList
from sqlalchemy.orm import relationship
from typing import Any, List


from eNMS.database import SMALL_STRING_LENGTH
from eNMS.database.associations import pool_user_table
from eNMS.database.base import AbstractBase


class Server(AbstractBase):

    __tablename__ = type = "Server"
    id = Column(Integer, primary_key=True)
    name = Column(SmallString, unique=True)
    description = Column(SmallString, default="")
    ip_address = Column(SmallString, default="")
    weight = Column(Integer, default=1)
    status = Column(SmallString, default="down")
    cpu_load = Column(Float, default=0.0)

    def generate_row(self, table: str) -> List[str]:
        return [
            f"""<button type="button" class="btn btn-primary btn-xs"
            onclick="showTypePanel('server', '{self.id}')">Edit</button>""",
            f"""<button type="button" class="btn btn-primary btn-xs"
            onclick="showTypePanel('server', '{self.id}', 'duplicate')">
            Duplicate</button>""",
            f"""<button type="button" class="btn btn-danger btn-xs"
            onclick="showDeletionPanel('server', '{self.id}', '{self.name}')">
            Delete</button>""",
        ]


class Parameters(AbstractBase):

    __tablename__ = type = "Parameters"
    id = Column(Integer, primary_key=True)
    name = Column(SmallString, default="default", unique=True)
    cluster_scan_subnet = Column(SmallString, default="")
    cluster_scan_protocol = Column(SmallString, default="")
    cluster_scan_timeout = Column(Float, default=0.0)
    custom_config = Column(MutableDict, default={})
    default_longitude = Column(Float, default=0.0)
    default_latitude = Column(Float, default=0.0)
    default_zoom_level = Column(Integer, default=0)
    default_view = Column(SmallString, default="")
    default_marker = Column(SmallString, default="")
    git_configurations = Column(SmallString, default="")
    git_automation = Column(SmallString, default="")
    gotty_start_port = Column(Integer, default=0)
    gotty_end_port = Column(Integer, default=0)
    gotty_port_index = Column(Integer, default=-1)
    opennms_rest_api = Column(
        SmallString, default="https://demo.opennms.org/opennms/rest"
    )
    opennms_devices = Column(
        SmallString,
        default="https://demo.opennms.org/opennms/rest/nodes",
    )
    opennms_login = Column(SmallString, default="demo")
    mail_sender = Column(SmallString, default="")
    mail_recipients = Column(SmallString, default="")
    mattermost_url = Column(SmallString, default="")
    mattermost_channel = Column(SmallString, default="")
    mattermost_verify_certificate = Column(Boolean, default=False)
    slack_token = Column(SmallString)
    slack_channel = Column(SmallString, default="")

    def update(self, **kwargs: Any) -> None:
        self.gotty_port_index = -1
        super().update(**kwargs)


class User(AbstractBase, UserMixin):

    __tablename__ = type = "User"
    id = Column(Integer, primary_key=True)
    email = Column(SmallString, default="")
    name = Column(SmallString, default="")
    permissions = Column(MutableList, default=[])
    pools = relationship("Pool", secondary=pool_user_table, back_populates="users")
    password = Column(SmallString, default="")

    def generate_row(self, table: str) -> List[str]:
        return [
            f"""<button type="button" class="btn btn-primary btn-xs"
            onclick="showTypePanel('user', '{self.id}')">Edit</button>""",
            f"""<button type="button" class="btn btn-primary btn-xs"
            onclick="showTypePanel('user', '{self.id}', 'duplicate')">
            Duplicate</button>""",
            f"""<button type="button" class="btn btn-danger btn-xs"
            onclick="showDeletionPanel('user', '{self.id}', '{self.name}')">
            Delete</button>""",
        ]

    @property
    def is_admin(self) -> bool:
        return "Admin" in self.permissions

    def allowed(self, permission: str) -> bool:
        return self.is_admin or permission in self.permissions
