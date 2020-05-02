from collections import defaultdict
from datetime import datetime
from flask_login import UserMixin
from itertools import chain
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
    email = db.Column(db.SmallString)
    password = db.Column(db.SmallString)
    authentication = db.Column(db.SmallString, default="database")
    groups = db.Column(db.List)
    rbac = db.Column(db.Dict)
    small_menu = db.Column(Boolean, default=False, info={"dont_track_changes": True})
    groups = relationship(
        "Group", secondary=db.user_group_table, back_populates="users"
    )

    def update(self, **kwargs):
        if app.settings["security"]["hash_user_passwords"] and "password" in kwargs:
            kwargs["password"] = argon2.hash(kwargs["password"])
        super().update(**kwargs)
        self.rbac = self.compute_rbac()

    def compute_rbac(self):
        rbac = defaultdict(list)
        for group in self.groups:
            for access in app.rbac:
                rbac[access].extend(getattr(group, access))
        return rbac


@db.set_custom_properties
class Group(AbstractBase):

    __tablename__ = type = "group"
    id = db.Column(Integer, primary_key=True)
    name = db.Column(db.SmallString, unique=True)
    email = db.Column(db.SmallString)
    menu = db.Column(db.List)
    pages = db.Column(db.List)
    upper_menu = db.Column(db.List)
    get_requests = db.Column(db.List)
    post_requests = db.Column(db.List)
    users = relationship(
        "User", secondary=db.user_group_table, back_populates="groups"
    )


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
