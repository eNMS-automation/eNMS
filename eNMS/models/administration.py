from datetime import datetime
from flask_login import UserMixin
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
    permissions = db.Column(db.List)
    password = db.Column(db.SmallString)
    group = db.Column(db.SmallString)
    small_menu = db.Column(Boolean, default=False, info={"dont_track_changes": True})

    def update(self, **kwargs):
        if app.settings["security"]["hash_user_passwords"] and "password" in kwargs:
            kwargs["password"] = argon2.hash(kwargs["password"])
        super().update(**kwargs)

    @property
    def is_admin(self):
        return "Admin" in self.permissions

    def allowed(self, permission):
        return self.is_admin or permission in self.permissions


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
