from flask_login import UserMixin
from itertools import chain
from os.path import exists, getmtime
from passlib.hash import argon2
from pathlib import Path
from shutil import move, rmtree
from sqlalchemy import Boolean, ForeignKey, Integer
from sqlalchemy.orm import relationship
from time import ctime

from eNMS.database import db
from eNMS.models.base import AbstractBase
from eNMS.variables import vs


class Server(AbstractBase):

    __tablename__ = type = "server"
    id = db.Column(Integer, primary_key=True)
    name = db.Column(db.SmallString, unique=True)
    description = db.Column(db.LargeString)
    mac_address = db.Column(db.TinyString)
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
    landing_page = db.Column(db.SmallString, default="/dashboard")
    password = db.Column(db.SmallString)
    authentication = db.Column(db.TinyString)
    menu = db.Column(db.List)
    pages = db.Column(db.List)
    get_requests = db.Column(db.List)
    post_requests = db.Column(db.List)
    delete_requests = db.Column(db.List)
    small_menu = db.Column(Boolean, default=False, info={"log_change": False})
    theme = db.Column(db.TinyString, default="default", info={"log_change": False})
    groups = relationship("Group", secondary=db.user_group_table, back_populates="users")
    services = relationship(
        "Service", secondary=db.service_owner_table, back_populates="owners"
    )
    is_admin = db.Column(Boolean, default=False)

    def get_id(self):
        return self.name

    def update(self, **kwargs):
        if (
            vs.settings["security"]["hash_user_passwords"]
            and kwargs.get("password")
            and not kwargs["password"].startswith("$argon2i")
        ):
            kwargs["password"] = argon2.hash(kwargs["password"])
        super().update(**kwargs)


class Group(AbstractBase):

    __tablename__ = type = class_type = "group"
    id = db.Column(Integer, primary_key=True)
    name = db.Column(db.SmallString, unique=True)
    description = db.Column(db.LargeString)
    email = db.Column(db.SmallString)
    creator = db.Column(db.SmallString)
    users = relationship("User", secondary=db.user_group_table, back_populates="groups")


class Access(AbstractBase):

    __tablename__ = type = class_type = "access"
    id = db.Column(Integer, primary_key=True)
    name = db.Column(db.SmallString, unique=True)
    description = db.Column(db.LargeString)
    menu = db.Column(db.List)
    pages = db.Column(db.List)
    get_requests = db.Column(db.List)
    post_requests = db.Column(db.List)
    delete_requests = db.Column(db.List)


class Credential(AbstractBase):

    __tablename__ = type = class_type = "credential"
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
        super().update(**{"time": vs.get_time(), **kwargs})


class Parameters(AbstractBase):

    __tablename__ = type = "parameters"
    id = db.Column(Integer, primary_key=True)
    banner_active = db.Column(Boolean)
    banner_deactivate_on_restart = db.Column(Boolean)
    banner_properties = db.Column(db.Dict)


class File(AbstractBase):

    __tablename__ = type = "file"
    type = db.Column(db.SmallString)
    __mapper_args__ = {"polymorphic_identity": "file", "polymorphic_on": type}
    id = db.Column(Integer, primary_key=True)
    name = db.Column(db.SmallString, unique=True)
    filename = db.Column(db.SmallString)
    path = db.Column(db.SmallString, unique=True)
    last_modified = db.Column(db.TinyString)
    last_updated = db.Column(db.TinyString)
    status = db.Column(db.TinyString)
    folder_id = db.Column(Integer, ForeignKey("folder.id"))
    folder = relationship(
        "Folder", foreign_keys="Folder.folder_id", back_populates="files"
    )
    folder_path = db.Column(db.SmallString)

    def delete(self):
        Path(self.path).unlink()

    def update(self, move_file=True, **kwargs):
        old_path = self.path
        super().update(**kwargs)
        if exists(str(old_path)) and not exists(self.path) and move_file:
            move(old_path, self.path)
        self.name = self.path.replace("/", ">")
        *split_folder_path, self.filename = self.path.split("/")
        self.folder_path = "/".join(split_folder_path)
        self.folder = db.fetch("folder", path=self.folder_path, allow_none=True)
        self.last_modified = ctime(getmtime(self.path))
        self.last_updated = ctime()
        self.status = "Updated"


class Folder(File):

    __tablename__ = "folder"
    pretty_name = "Folder"
    parent_type = "file"
    id = db.Column(Integer, ForeignKey("file.id"), primary_key=True)
    files = relationship(
        "File",
        back_populates="folder",
        foreign_keys="File.folder_id",
        cascade="all, delete-orphan",
    )
    __mapper_args__ = {
        "polymorphic_identity": "folder",
        "inherit_condition": id == File.id,
    }

    def delete(self):
        rmtree(self.path, ignore_errors=True)
