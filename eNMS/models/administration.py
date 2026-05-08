from datetime import datetime
from flask_login import current_user, UserMixin
from itertools import chain
from os import kill, makedirs
from os.path import exists, getmtime, getsize
from passlib.hash import argon2
from pathlib import Path
from shutil import move, rmtree
from signal import SIGTERM
from sqlalchemy import Boolean, Float, ForeignKey, Integer
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import relationship
from sqlalchemy.types import JSON
from time import ctime

from eNMS.database import db
from eNMS.environment import env
from eNMS.models.base import AbstractBase
from eNMS.variables import vs


class Snippet(AbstractBase):
    __tablename__ = type = class_type = "snippet"
    id = db.Column(Integer, primary_key=True)
    name = db.Column(db.SmallString, unique=True)
    category = db.Column(db.SmallString)
    creator = db.Column(db.SmallString)
    creation_time = db.Column(db.TinyString)
    code = db.Column(db.LargeString)
    description = db.Column(db.LargeString)
    version = db.Column(db.TinyString)
    last_modified = db.Column(db.TinyString, info={"log_change": False})
    last_modified_by = db.Column(db.SmallString, info={"log_change": False})
    logs = relationship("Changelog", back_populates="snippet")


class Server(AbstractBase):
    __tablename__ = type = class_type = "server"
    id = db.Column(Integer, primary_key=True)
    name = db.Column(db.SmallString, unique=True)
    creator = db.Column(db.SmallString)
    creation_time = db.Column(db.TinyString)
    description = db.Column(db.LargeString)
    role = db.Column(db.TinyString, default="primary")
    mac_address = db.Column(db.TinyString)
    ip_address = db.Column(db.TinyString)
    scheduler_address = db.Column(db.TinyString)
    scheduler_active = db.Column(Boolean, default=True)
    location = db.Column(db.SmallString)
    version = db.Column(db.TinyString)
    commit_sha = db.Column(db.TinyString)
    last_modified = db.Column(db.TinyString, info={"log_change": False})
    last_modified_by = db.Column(db.SmallString, info={"log_change": False})
    last_restart = db.Column(db.TinyString)
    weight = db.Column(Integer, default=1)
    allowed_automation = db.Column(db.List)
    status = db.Column(db.TinyString, default="down")
    logs = relationship("Changelog", back_populates="server")
    runs = relationship("Run", back_populates="server")
    workers = relationship("Worker", back_populates="server")
    sessions = relationship("Session", back_populates="server")
    model_properties = {"current_runs": "str"}

    @property
    def current_runs(self):
        return (
            db.query("run", rbac=None, properties=["id"])
            .filter_by(server_id=self.id, status="Running")
            .count()
        )


class Worker(AbstractBase):
    __tablename__ = type = class_type = "worker"
    id = db.Column(Integer, primary_key=True)
    name = db.Column(db.SmallString, unique=True)
    process_id = db.Column(Integer)
    description = db.Column(db.LargeString)
    subtype = db.Column(db.TinyString)
    last_update = db.Column(db.TinyString)
    runs = relationship("Run", back_populates="worker")
    server_id = db.Column(Integer, ForeignKey("server.id"))
    server = relationship("Server", back_populates="workers")
    server_name = association_proxy("server", "name")
    model_properties = {"current_runs": "str", "server_properties": "dict"}

    def update(self, **kwargs):
        self.last_update = vs.get_time()
        super().update(**kwargs)

    def delete(self):
        try:
            env.log("critical", f"Sending SIGTERM signal to process ID {self.name}")
            kill(int(self.process_id), SIGTERM)
        except Exception as exc:
            return {"log": f"Failed to deleted process: {exc}"}

    @property
    def server_properties(self):
        return self.server.base_properties

    @property
    def current_runs(self):
        return (
            db.query("run", rbac=None, properties=["id"])
            .filter_by(worker_id=self.id, status="Running")
            .count()
        )


class User(AbstractBase, UserMixin):
    __tablename__ = type = class_type = "user"
    id = db.Column(Integer, primary_key=True)
    name = db.Column(db.SmallString, unique=True)
    creator = db.Column(db.SmallString)
    creation_time = db.Column(db.TinyString)
    description = db.Column(db.LargeString)
    groups = db.Column(db.LargeString)
    is_admin = db.Column(Boolean, default=False)
    last_login = db.Column(db.SmallString)
    last_modified = db.Column(db.TinyString, info={"log_change": False})
    last_modified_by = db.Column(db.SmallString, info={"log_change": False})
    email = db.Column(db.SmallString)
    landing_page = db.Column(
        db.SmallString, default=vs.settings["authentication"]["landing_page"]
    )
    display_tree = db.Column(Boolean, default=False)
    password = db.Column(db.SmallString)
    authentication = db.Column(db.TinyString, default="database")
    small_menu = db.Column(Boolean, default=False, info={"log_change": False})
    theme = db.Column(
        db.TinyString, default=vs.settings["app"]["theme"], info={"log_change": False}
    )
    zoom_sensitivity = db.Column(Float, default=1, info={"log_change": False})
    groups = relationship(
        "Group", secondary=db.user_group_table, back_populates="users"
    )
    logs = relationship("Changelog", back_populates="user")

    @classmethod
    def database_init(cls):
        for property in vs.rbac["form_properties"]:
            setattr(cls, property, db.Column(db.List))

    def delete(self):
        if self.name == getattr(current_user, "name", False):
            return {"log": "A user cannot be deleted while logged in."}

    def get_id(self):
        return self.name

    def post_update(self):
        self.update_rbac()

    def update(self, **kwargs):
        if not getattr(current_user, "is_admin", True):
            properties = ["is_admin", "groups"]
            allow_password_change = vs.settings["authentication"][
                "allow_password_change"
            ]
            if not allow_password_change or self.authentication != "database":
                properties.append("password")
            for property in properties:
                kwargs.pop(property, None)
        if kwargs.get("password") and not kwargs["password"].startswith("$argon2i"):
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
    creation_time = db.Column(db.TinyString)
    admin_only = db.Column(Boolean, default=False)
    force_read_access = db.Column(Boolean, default=False)
    description = db.Column(db.LargeString)
    email = db.Column(db.SmallString)
    last_modified = db.Column(db.TinyString, info={"log_change": False})
    last_modified_by = db.Column(db.SmallString, info={"log_change": False})
    users = relationship("User", secondary=db.user_group_table, back_populates="groups")
    logs = relationship("Changelog", back_populates="group")

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
                        "".join(word.capitalize() for word in model.split("_")),
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
    creation_time = db.Column(db.TinyString)
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
    logs = relationship("Changelog", back_populates="credential")


class Changelog(AbstractBase):
    __tablename__ = class_type = "changelog"
    log_change = False
    type = db.Column(db.SmallString)
    __mapper_args__ = {"polymorphic_identity": "changelog", "polymorphic_on": type}
    id = db.Column(Integer, primary_key=True)
    name = db.Column(db.MediumString)
    time = db.Column(db.TinyString, index=True)
    content = db.Column(db.LargeString)
    severity = db.Column(db.TinyString, default="debug")
    author = db.Column(db.SmallString)
    history = db.Column(JSON, default={})
    is_revertible = db.Column(Boolean, default=False)
    source = db.Column(db.SmallString)
    target_id = db.Column(Integer)
    target_type = db.Column(db.SmallString)
    target_name = db.Column(db.MediumString)
    workflows = relationship(
        "Workflow",
        secondary=db.changelog_workflow_table,
        back_populates="service_changelogs",
    )
    networks = relationship(
        "Network",
        secondary=db.changelog_network_table,
        back_populates="device_changelogs",
    )

    @classmethod
    def database_init(cls):
        for model, class_name in vs.database["changelog_models"].items():
            kwargs = {"back_populates": "logs", "foreign_keys": f"Changelog.{model}_id"}
            setattr(
                cls,
                f"{model}_id",
                db.Column(
                    Integer, ForeignKey(f"{model}.id", ondelete="SET NULL"), index=True
                ),
            )
            setattr(cls, model, relationship(class_name, **kwargs))

    def __repr__(self):
        return self.content

    def update(self, **kwargs):
        kwargs["time"] = vs.get_time()
        if not kwargs.get("author"):
            kwargs["author"] = getattr(current_user, "name", "")
        super().update(**kwargs)
        self.is_revertible = bool(self.history and self.author)
        self.name = f"{self.target_name} updated by {self.author}"


class Parameters(AbstractBase):
    __tablename__ = type = class_type = "parameters"
    id = db.Column(Integer, primary_key=True)
    name = db.Column(db.SmallString, unique=True)
    banner_active = db.Column(Boolean)
    banner_deactivate_on_restart = db.Column(Boolean)
    banner_properties = db.Column(db.Dict)


class File(AbstractBase):
    __tablename__ = class_type = export_type = "file"
    log_change = vs.settings["files"]["log_events"]
    type = db.Column(db.SmallString)
    __mapper_args__ = {"polymorphic_identity": "file", "polymorphic_on": type}
    id = db.Column(Integer, primary_key=True)
    name = db.Column(db.SmallString, unique=True)
    description = db.Column(db.LargeString)
    filename = db.Column(db.SmallString, index=True)
    path = db.Column(db.SmallString, unique=True)
    full_path = db.Column(db.SmallString, unique=True, info={"log_change": False})
    creation_time = db.Column(db.TinyString)
    last_modified = db.Column(db.TinyString, info={"log_change": False})
    last_updated = db.Column(db.TinyString)
    size = db.Column(db.SmallString)
    status = db.Column(db.TinyString)
    folder_path = db.Column(db.SmallString, index=True, info={"log_change": False})
    logs = relationship("Changelog", back_populates="file")

    def update(self, move_file=True, **kwargs):
        old_path = self.full_path
        self.full_path = f"{vs.file_path}{kwargs['path']}"
        super().update(**kwargs)
        self.name = self.path.replace("/", ">")
        *split_folder_path, self.filename = self.full_path.split("/")
        self.folder_path = "/".join(split_folder_path)
        if kwargs.get("migration_import"):
            return
        if not str(Path(self.full_path).resolve()).startswith(f"{vs.file_path}/"):
            raise Exception("The path resolves outside of the files folder.")
        if exists(str(old_path)) and not exists(self.full_path) and move_file:
            move(old_path, self.full_path)
        if exists(self.full_path) and not kwargs.get("migration_import"):
            last_modified = datetime.strptime(ctime(getmtime(self.full_path)), "%c")
            self.last_modified = str(last_modified)
            self.size = getsize(self.full_path)
        if not kwargs.get("migration_import"):
            self.last_updated = str(datetime.strptime(ctime(), "%c"))
        self.status = "Updated"

    def delete(self):
        trash = vs.settings["files"]["trash"]
        if not exists(self.full_path) or not trash:
            return
        if self.full_path == trash:
            return {"log": "Cannot delete the 'trash' folder."}
        if trash in self.full_path:
            if self.type == "folder":
                rmtree(self.full_path, ignore_errors=True)
            else:
                Path(self.full_path).unlink(missing_ok=True)
        else:
            now = vs.get_time().replace(":", "-")
            filename = f"{now}-{self.filename}"
            if str(vs.file_path) in trash:
                trash_scoped_path = trash.replace(str(vs.file_path), "")
                self.update(path=f"{trash_scoped_path}/{filename}")
                log = f"File '{filename}' moved to 'trash' folder."
                return {"log_level": "warning", "log": log}
            else:
                move(self.full_path, f"{trash}/{filename}")


class GenericFile(File):
    __tablename__ = "generic_file"
    __mapper_args__ = {"polymorphic_identity": "generic_file"}
    pretty_name = "Generic File"
    parent_type = "file"
    id = db.Column(Integer, ForeignKey("file.id", ondelete="cascade"), primary_key=True)


class Folder(File):
    __tablename__ = "folder"
    __mapper_args__ = {"polymorphic_identity": "folder"}
    pretty_name = "Folder"
    id = db.Column(Integer, ForeignKey("file.id", ondelete="cascade"), primary_key=True)

    def __init__(self, **kwargs):
        full_path = f"{vs.file_path}{kwargs['path']}"
        self.update(**kwargs)
        if not exists(full_path) and not kwargs.get("migration_import"):
            makedirs(full_path)


class Data(AbstractBase):
    __tablename__ = type = class_type = export_type = "data"
    type = db.Column(db.SmallString)
    __mapper_args__ = {"polymorphic_identity": "data", "polymorphic_on": type}
    id = db.Column(Integer, primary_key=True)
    persistent_id = db.Column(db.TinyString)
    name = db.Column(db.SmallString, unique=True)
    path = db.Column(db.SmallString, unique=True)
    scoped_name = db.Column(db.SmallString, default="")
    description = db.Column(db.LargeString)
    creator = db.Column(db.SmallString)
    creation_time = db.Column(db.TinyString)
    last_modified = db.Column(db.TinyString, info={"log_change": False})
    last_modified_by = db.Column(db.SmallString, info={"log_change": False})
    store_id = db.Column(Integer, ForeignKey("store.id", ondelete="SET NULL"))
    store = relationship("Store", back_populates="data", foreign_keys="Data.store_id")
    logs = relationship("Changelog", back_populates="data")
    model_properties = {"ui_name": "str"}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.persistent_id:
            self.persistent_id = vs.get_persistent_id()

    def update(self, **kwargs):
        super().update(**kwargs)
        if not kwargs.get("migration_import"):
            self.post_update()

    def post_update(self):
        if self.store:
            self.path = f"{self.store.path}/{self.scoped_name}"
        else:
            self.path = f"/{self.scoped_name}"
        self.name = self.path.replace("/", ">")

    @property
    def ui_name(self):
        return self.path
