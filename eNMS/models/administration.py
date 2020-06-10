from datetime import datetime
from flask_login import UserMixin
from passlib.hash import argon2
from sqlalchemy import Boolean, Integer
from sqlalchemy.orm import relationship

from eNMS import app
from eNMS.database import db
from eNMS.models.base import AbstractBase


@db.set_custom_properties
class Server(AbstractBase):

    __tablename__ = type = "server"
    id = db.Column(Integer, primary_key=True)
    name = db.Column(db.SmallString, unique=True)
    description = db.Column(db.SmallString)
    ip_address = db.Column(db.SmallString)
    weight = db.Column(Integer, default=1)
    status = db.Column(db.SmallString, default="down")


@db.set_custom_properties
class User(AbstractBase, UserMixin):

    __tablename__ = type = "user"
    id = db.Column(Integer, primary_key=True)
    name = db.Column(db.SmallString, unique=True)
    is_admin = db.Column(Boolean)
    email = db.Column(db.SmallString)
    password = db.Column(db.SmallString)
    authentication = db.Column(db.SmallString, default="database")
    groups = db.Column(db.List)
    menu = db.Column(db.List)
    pages = db.Column(db.List)
    upper_menu = db.Column(db.List)
    get_requests = db.Column(db.List)
    post_requests = db.Column(db.List)
    small_menu = db.Column(Boolean, default=False, info={"dont_track_changes": True})
    theme = db.Column(
        db.SmallString, default="default", info={"dont_track_changes": True}
    )
    groups = relationship(
        "Group", secondary=db.user_group_table, back_populates="users"
    )
    access = relationship(
        "Access", secondary=db.access_user_table, back_populates="users"
    )
    is_admin = db.Column(Boolean, default=False)

    def get_id(self):
        return self.name

    def update(self, **kwargs):
        if app.settings["security"]["hash_user_passwords"] and kwargs.get("password"):
            kwargs["password"] = argon2.hash(kwargs["password"])
        super().update(**kwargs)
        self.update_rbac()

    def update_rbac(self):
        if self.is_admin:
            return
        for access_type in app.rbac:
            group_access = (getattr(group, access_type) for group in self.groups)
            setattr(self, access_type, list(set().union(*group_access)))


@db.set_custom_properties
class Group(AbstractBase):

    __tablename__ = type = "group"
    id = db.Column(Integer, primary_key=True)
    name = db.Column(db.SmallString, unique=True)
    email = db.Column(db.SmallString)
    users = relationship("User", secondary=db.user_group_table, back_populates="groups")
    access = relationship(
        "Access", secondary=db.access_group_table, back_populates="groups"
    )

    def update(self, **kwargs):
        super().update(**kwargs)


@db.set_custom_properties
class Access(AbstractBase):

    __tablename__ = type = "access"
    id = db.Column(Integer, primary_key=True)
    name = db.Column(db.SmallString, unique=True)
    menu = db.Column(db.List)
    pages = db.Column(db.List)
    upper_menu = db.Column(db.List)
    get_requests = db.Column(db.List)
    post_requests = db.Column(db.List)
    users = relationship(
        "User", secondary=db.access_user_table, back_populates="access"
    )
    groups = relationship(
        "Group", secondary=db.access_group_table, back_populates="access"
    )
    pools = relationship(
        "Pool", secondary=db.access_pool_table, back_populates="access"
    )
    services = relationship(
        "Service", secondary=db.access_service_table, back_populates="access"
    )
    devices = relationship(
        "Device", secondary=db.access_device_table, back_populates="access"
    )
    links = relationship(
        "Link", secondary=db.access_link_table, back_populates="access"
    )

    def update(self, **kwargs):
        super().update(**kwargs)
        self.update_rbac()

    def update_rbac(self):
        for user in self.users:
            user.update_rbac()


@db.set_custom_properties
class Changelog(AbstractBase):

    __tablename__ = "changelog"
    type = db.Column(db.SmallString)
    __mapper_args__ = {"polymorphic_identity": "changelog", "polymorphic_on": type}
    id = db.Column(Integer, primary_key=True)
    time = db.Column(db.SmallString)
    content = db.Column(db.LargeString)
    severity = db.Column(db.SmallString, default="debug")
    user = db.Column(db.SmallString, default="admin")

    def update(self, **kwargs):
        kwargs["time"] = str(datetime.now())
        super().update(**kwargs)
