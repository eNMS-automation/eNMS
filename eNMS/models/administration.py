from flask_login import current_user, UserMixin
from datetime import datetime
from itertools import chain
from os import makedirs
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
    creator = db.Column(db.SmallString)
    description = db.Column(db.LargeString)
    mac_address = db.Column(db.TinyString)
    ip_address = db.Column(db.TinyString)
    weight = db.Column(Integer, default=1)
    status = db.Column(db.TinyString, default="down")


class User(AbstractBase, UserMixin):

    __tablename__ = type = class_type = "user"
    id = db.Column(Integer, primary_key=True)
    name = db.Column(db.SmallString, unique=True)
    creator = db.Column(db.SmallString)
    description = db.Column(db.LargeString)
    groups = db.Column(db.LargeString)
    is_admin = db.Column(Boolean, default=False)
    email = db.Column(db.SmallString)
    landing_page = db.Column(
        db.SmallString, default=vs.settings["authentication"]["landing_page"]
    )
    password = db.Column(db.SmallString)
    authentication = db.Column(db.TinyString, default="database")
    small_menu = db.Column(Boolean, default=False, info={"log_change": False})
    theme = db.Column(db.TinyString, default="default", info={"log_change": False})
    groups = relationship(
        "Group", secondary=db.user_group_table, back_populates="users"
    )

    @classmethod
    def database_init(cls):
        for property in vs.rbac["form_properties"]:
            setattr(cls, property, db.Column(db.List))

    def delete(self):
        if self.name == getattr(current_user, "name", False):
            raise db.rbac_error("A user cannot be deleted while logged in.")

    def get_id(self):
        return self.name

    def post_update(self):
        self.update_rbac()
        return self.get_properties()

    def update(self, **kwargs):
        if (
            vs.settings["security"]["hash_user_passwords"]
            and kwargs.get("password")
            and not kwargs["password"].startswith("$argon2i")
        ):
            kwargs["password"] = argon2.hash(kwargs["password"])
        super().update(**kwargs)

    def update_rbac(self):
        if self.is_admin:
            return
        for property in vs.rbac["form_properties"]:
            group_value = (getattr(group, property) for group in self.groups)
            setattr(self, property, list(set(chain.from_iterable(group_value))))


class Group(AbstractBase):

    __tablename__ = type = class_type = "group"
    id = db.Column(Integer, primary_key=True)
    name = db.Column(db.SmallString, unique=True)
    creator = db.Column(db.SmallString)
    description = db.Column(db.LargeString)
    email = db.Column(db.SmallString)
    users = relationship("User", secondary=db.user_group_table, back_populates="groups")
    credentials = relationship(
        "Credential", secondary=db.credential_group_table, back_populates="groups"
    )

    @classmethod
    def database_init(cls):
        for property in vs.rbac["form_properties"]:
            setattr(cls, property, db.Column(db.List))
        for model, properties in vs.rbac["rbac_models"].items():
            setattr(cls, f"{model}_access", db.Column(db.List))
            for property in properties:
                setattr(
                    cls,
                    f"{property}_{model}s",
                    relationship(
                        model.capitalize(),
                        secondary=getattr(db, f"{model}_{property}_table"),
                        back_populates=property,
                    ),
                )
        for property in vs.rbac["rbac_models"]["device"]:
            setattr(
                cls,
                f"rbac_pool_{property}",
                relationship(
                    "Pool",
                    secondary=getattr(db, f"pool_group_{property}_table"),
                    back_populates=f"rbac_group_{property}",
                ),
            )

    def update(self, **kwargs):
        old_users = set(self.users)
        super().update(**kwargs)
        if not kwargs.get("import_mechanism", False):
            for user in set(self.users) | old_users:
                user.update_rbac()


class Credential(AbstractBase):

    __tablename__ = type = class_type = "credential"
    id = db.Column(Integer, primary_key=True)
    name = db.Column(db.SmallString, unique=True)
    creator = db.Column(db.SmallString)
    last_modified = db.Column(db.TinyString, info={"log_change": False})
    last_modified_by = db.Column(db.SmallString, info={"log_change": False})
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
    groups = relationship(
        "Group",
        secondary=db.credential_group_table,
        back_populates="credentials",
    )

    def update(self, **kwargs):
        super().update(**kwargs)
        if not kwargs.get("migration_import"):
            self.update_last_modified_properties()


class Changelog(AbstractBase):

    __tablename__ = "changelog"
    type = db.Column(db.SmallString)
    __mapper_args__ = {"polymorphic_identity": "changelog", "polymorphic_on": type}
    id = db.Column(Integer, primary_key=True)
    time = db.Column(db.TinyString, index=True)
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

    __tablename__ = type = class_type = "file"
    type = db.Column(db.SmallString)
    __mapper_args__ = {"polymorphic_identity": "file", "polymorphic_on": type}
    id = db.Column(Integer, primary_key=True)
    name = db.Column(db.SmallString, unique=True)
    description = db.Column(db.LargeString)
    filename = db.Column(db.SmallString, index=True)
    path = db.Column(db.SmallString, unique=True)
    last_modified = db.Column(db.TinyString, info={"log_change": False})
    last_updated = db.Column(db.TinyString)
    status = db.Column(db.TinyString)
    folder_id = db.Column(Integer, ForeignKey("folder.id"))
    folder = relationship(
        "Folder", foreign_keys="Folder.folder_id", back_populates="files"
    )
    folder_path = db.Column(db.SmallString)

    def update(self, move_file=True, **kwargs):
        old_path = self.path
        super().update(**kwargs)
        if exists(str(old_path)) and not exists(self.path) and move_file:
            move(old_path, self.path)
        self.name = self.path.replace("/", ">")
        *split_folder_path, self.filename = self.path.split("/")
        self.folder_path = "/".join(split_folder_path)
        self.folder = db.fetch("folder", path=self.folder_path, allow_none=True)
        self.last_modified = datetime.strptime(ctime(getmtime(self.path)), "%c")
        if not kwargs.get("migration_import"):
            self.last_updated = datetime.strptime(ctime(), "%c")
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

    def __init__(self, **kwargs):
        if not exists(kwargs["path"]):
            makedirs(kwargs["path"])
        self.update(**kwargs)
