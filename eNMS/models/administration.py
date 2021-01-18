from datetime import datetime
from flask_login import UserMixin
from itertools import chain
from passlib.hash import argon2
from sqlalchemy import Boolean, Integer
from sqlalchemy.orm import relationship

from eNMS import app
from eNMS.database import db
from eNMS.models import models
from eNMS.models.base import AbstractBase
from eNMS.setup import rbac


class Server(AbstractBase):

    __tablename__ = type = "server"
    id = db.Column(Integer, primary_key=True)
    name = db.Column(db.SmallString, unique=True)
    description = db.Column(db.LargeString)
    ip_address = db.Column(db.TinyString)
    weight = db.Column(Integer, default=1)
    status = db.Column(db.TinyString, default="down")


class User(AbstractBase, UserMixin):

    __tablename__ = type = class_type = "user"
    id = db.Column(Integer, primary_key=True)
    name = db.Column(db.SmallString, unique=True)
    description = db.Column(db.LargeString)
    groups = db.Column(db.LargeString)
    is_admin = db.Column(Boolean, default=False)
    email = db.Column(db.SmallString)
    password = db.Column(db.SmallString)
    authentication = db.Column(db.TinyString)
    menu = db.Column(db.List)
    pages = db.Column(db.List)
    upper_menu = db.Column(db.List)
    get_requests = db.Column(db.List)
    post_requests = db.Column(db.List)
    delete_requests = db.Column(db.List)
    small_menu = db.Column(Boolean, default=False, info={"dont_track_changes": True})
    theme = db.Column(
        db.TinyString, default="default", info={"dont_track_changes": True}
    )
    pools = relationship("Pool", secondary=db.pool_user_table, back_populates="users")
    is_admin = db.Column(Boolean, default=False)

    def get_id(self):
        return self.name

    def update(self, **kwargs):
        if (
            app.settings["security"]["hash_user_passwords"]
            and kwargs.get("password")
            and not kwargs["password"].startswith("$argon2i")
        ):
            kwargs["password"] = argon2.hash(kwargs["password"])
        super().update(**kwargs)
        if not kwargs.get("import_mechanism", False):
            self.update_rbac()

    def update_rbac(self):
        if self.is_admin:
            return
        db.session.commit()
        user_access = (
            db.session.query(models["access"])
            .join(models["pool"], models["access"].user_pools)
            .join(models["user"], models["pool"].users)
            .filter(models["user"].name == self.name)
            .all()
        )
        for property in rbac:
            access_value = (getattr(access, property) for access in user_access)
            setattr(self, property, list(set(chain.from_iterable(access_value))))


class Access(AbstractBase):

    __tablename__ = type = "access"
    id = db.Column(Integer, primary_key=True)
    name = db.Column(db.SmallString, unique=True)
    description = db.Column(db.LargeString)
    menu = db.Column(db.List)
    pages = db.Column(db.List)
    upper_menu = db.Column(db.List)
    get_requests = db.Column(db.List)
    post_requests = db.Column(db.List)
    delete_requests = db.Column(db.List)
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


class Credential(AbstractBase):

    __tablename__ = type = "credential"
    id = db.Column(Integer, primary_key=True)
    name = db.Column(db.SmallString, unique=True)
    role = db.Column(db.SmallString, default="read-write")
    subtype = db.Column(db.SmallString, default="password")
    description = db.Column(db.LargeString)
    username = db.Column(db.SmallString)
    password = db.Column(db.SmallString)
    private_key = db.Column(db.LargeString)
    enable_password = db.Column(db.SmallString)
    priority = db.Column(Integer, default=1)
    device_pools = relationship(
        "Pool",
        secondary=db.credential_device_table,
        back_populates="credential_devices",
    )
    user_pools = relationship(
        "Pool",
        secondary=db.credential_user_table,
        back_populates="credential_users",
    )


class Changelog(AbstractBase):

    __tablename__ = "changelog"
    type = db.Column(db.SmallString)
    __mapper_args__ = {"polymorphic_identity": "changelog", "polymorphic_on": type}
    id = db.Column(Integer, primary_key=True)
    time = db.Column(db.TinyString)
    content = db.Column(db.LargeString)
    severity = db.Column(db.TinyString, default="debug")
    user = db.Column(db.SmallString, default="admin")

    def update(self, **kwargs):
        kwargs["time"] = str(datetime.now())
        super().update(**kwargs)
