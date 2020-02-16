from datetime import datetime
from flask_login import UserMixin
from sqlalchemy import Boolean, Integer

from eNMS.database.dialect import Column, MutableList, LargeString, SmallString
from eNMS.database.base import AbstractBase


class Server(AbstractBase):

    __tablename__ = type = "server"
    id = Column(Integer, primary_key=True)
    name = Column(SmallString, unique=True)
    description = Column(SmallString)
    ip_address = Column(SmallString)
    weight = Column(Integer, default=1)
    status = Column(SmallString, default="down")


class User(AbstractBase, UserMixin):

    __tablename__ = type = "user"
    id = Column(Integer, primary_key=True)
    name = Column(SmallString, unique=True)
    email = Column(SmallString)
    permissions = Column(MutableList)
    password = Column(SmallString)
    group = Column(SmallString)
    small_menu = Column(Boolean, default=False, info={"dont_track_changes": True})

    @property
    def is_admin(self):
        return "Admin" in self.permissions

    def allowed(self, permission):
        return self.is_admin or permission in self.permissions


class Changelog(AbstractBase):

    __tablename__ = "changelog"
    type = Column(SmallString)
    __mapper_args__ = {"polymorphic_identity": "changelog", "polymorphic_on": type}
    id = Column(Integer, primary_key=True)
    time = Column(SmallString)
    content = Column(LargeString, default="")
    severity = Column(SmallString, default="debug")
    user = Column(SmallString, default="admin")

    def update(self, **kwargs):
        kwargs["time"] = str(datetime.now())
        super().update(**kwargs)
