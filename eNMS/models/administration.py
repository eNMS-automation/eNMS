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

    __tablename__ = type = class_type = "user"
    id = db.Column(Integer, primary_key=True)
    name = db.Column(db.SmallString, unique=True)
    is_admin = db.Column(Boolean)
    email = db.Column(db.SmallString)
    password = db.Column(db.SmallString)
    authentication = db.Column(db.SmallString)
    menu = db.Column(db.List)
    pages = db.Column(db.List)
    upper_menu = db.Column(db.List)
    get_requests = db.Column(db.List)
    post_requests = db.Column(db.List)
    small_menu = db.Column(Boolean, default=False, info={"dont_track_changes": True})
    theme = db.Column(
        db.SmallString, default="default", info={"dont_track_changes": True}
    )
    pools = relationship("Pool", secondary=db.pool_user_table, back_populates="users")
    is_admin = db.Column(Boolean, default=False)

    def add_access(self, model, instance):
        for pool in self.pools:
            access = db.fetch("access", name=f"{pool.name}: {model}", allow_none=True)
            if not access:
                access = db.factory("access", name=f"{pool.name}: {model}")
                access.user_pools.append(pool)
                setattr(access, f"{model}_access", str(app.rbac["models"][model]))
            getattr(access, model).append(instance)

    def get_id(self):
        return self.name

    def update(self, **kwargs):
        if app.settings["security"]["hash_user_passwords"] and kwargs.get("password"):
            kwargs["password"] = argon2.hash(kwargs["password"])
        super().update(**kwargs)
        self.update_rbac()

    @property
    def user_access(self):
        for pool in self.pools:
            yield from pool.access

    def update_rbac(self):
        if self.is_admin:
            return
        for access_type in app.rbac:
            if not hasattr(self, access_type):
                continue
            result = (getattr(access, access_type) for access in self.user_access)
            setattr(self, access_type, list(set().union(*result)))


@db.set_custom_properties
class Access(AbstractBase):

    __tablename__ = type = "access"
    id = db.Column(Integer, primary_key=True)
    name = db.Column(db.SmallString, unique=True)
    description = db.Column(db.SmallString)
    menu = db.Column(db.List)
    pages = db.Column(db.List)
    upper_menu = db.Column(db.List)
    get_requests = db.Column(db.List)
    post_requests = db.Column(db.List)
    user_pools = relationship(
        "Pool", secondary=db.access_user_pools_table, back_populates="access_users"
    )
    access_pools = relationship(
        "Pool", secondary=db.access_model_pools_table, back_populates="access"
    )
    access_type = db.Column(db.SmallString)

    def get_users(self):
        return set(chain.from_iterable(pool.users for pool in self.user_pools))

    def update(self, **kwargs):
        old_users = self.get_users()
        super().update(**kwargs)
        for user in old_users | self.get_users():
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
