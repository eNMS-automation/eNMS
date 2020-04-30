from collections import defaultdict
from datetime import datetime
from flask_login import UserMixin
from itertools import chain
from passlib.hash import argon2
from sqlalchemy import Boolean, Integer

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
    groups = db.Column(db.List)
    rbac = db.Column(db.Dict)
    small_menu = db.Column(Boolean, default=False, info={"dont_track_changes": True})

    def update(self, **kwargs):
        if app.settings["security"]["hash_user_passwords"] and "password" in kwargs:
            kwargs["password"] = argon2.hash(kwargs["password"])
        self.rbac = self.get_user_rbac()
        super().update(**kwargs)

    def get_rbac(self):
        rbac = defaultdict(list)
        for group in self.groups:
            for access, forbidden_list in app.rbac["groups"][group].items():
                rbac[access].extend(forbidden_list)


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
