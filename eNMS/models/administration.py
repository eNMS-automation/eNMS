from flask import Flask
from flask_login import UserMixin
from git import Repo
from logging import info
from os import scandir, remove
from pathlib import Path
from sqlalchemy import Boolean, Column, Float, Integer, PickleType, String
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.orm import relationship
from typing import Any, List
from yaml import load

from eNMS.database.functions import fetch, fetch_all, Session, SMALL_STRING_LENGTH
from eNMS.models.associations import pool_user_table
from eNMS.models.base import AbstractBase


class Server(AbstractBase):

    __tablename__ = type = "Server"
    id = Column(Integer, primary_key=True)
    name = Column(String(SMALL_STRING_LENGTH), unique=True)
    description = Column(String(SMALL_STRING_LENGTH), default="")
    ip_address = Column(String(SMALL_STRING_LENGTH), default="")
    weight = Column(Integer, default=1)
    status = Column(String(SMALL_STRING_LENGTH), default="down")
    cpu_load = Column(Float, default=0.0)

    def generate_row(self, table: str) -> List[str]:
        return [
            f"""<button type="button" class="btn btn-primary btn-xs"
            onclick="showTypePanel('server', '{self.id}')">Edit</button>""",
            f"""<button type="button" class="btn btn-primary btn-xs"
            onclick="showTypePanel('server', '{self.id}', true)">
            Duplicate</button>""",
            f"""<button type="button" class="btn btn-danger btn-xs"
            onclick="showDeletionPanel('server', '{self.id}', '{self.name}')">
            Delete</button>""",
        ]


class Parameters(AbstractBase):

    __tablename__ = type = "Parameters"
    id = Column(Integer, primary_key=True)
    name = Column(String(SMALL_STRING_LENGTH), default="default", unique=True)
    cluster_scan_subnet = Column(String(SMALL_STRING_LENGTH), default="")
    cluster_scan_protocol = Column(String(SMALL_STRING_LENGTH), default="")
    cluster_scan_timeout = Column(Float, default=0.0)
    default_longitude = Column(Float, default=0.0)
    default_latitude = Column(Float, default=0.0)
    default_zoom_level = Column(Integer, default=0)
    default_view = Column(String(SMALL_STRING_LENGTH), default="")
    default_marker = Column(String(SMALL_STRING_LENGTH), default="")
    git_configurations = Column(String(SMALL_STRING_LENGTH), default="")
    git_automation = Column(String(SMALL_STRING_LENGTH), default="")
    gotty_start_port = Column(Integer, default=0)
    gotty_end_port = Column(Integer, default=0)
    gotty_port_index = Column(Integer, default=-1)
    opennms_rest_api = Column(
        String(SMALL_STRING_LENGTH), default="https://demo.opennms.org/opennms/rest"
    )
    opennms_devices = Column(
        String(SMALL_STRING_LENGTH),
        default="https://demo.opennms.org/opennms/rest/nodes",
    )
    opennms_login = Column(String(SMALL_STRING_LENGTH), default="demo")
    mail_sender = Column(String(SMALL_STRING_LENGTH), default="")
    mail_recipients = Column(String(SMALL_STRING_LENGTH), default="")
    mattermost_url = Column(String(SMALL_STRING_LENGTH), default="")
    mattermost_channel = Column(String(SMALL_STRING_LENGTH), default="")
    mattermost_verify_certificate = Column(Boolean, default=False)
    slack_token = Column(String(SMALL_STRING_LENGTH), default="")
    slack_channel = Column(String(SMALL_STRING_LENGTH), default="")

    def update(self, **kwargs: Any) -> None:
        self.gotty_port_index = -1
        super().update(**kwargs)

    def update_database_configurations_from_git(self, app: Flask) -> None:
        for dir in scandir(app.path / "git" / "configurations"):
            if dir.name == ".git":
                continue
            device = fetch("Device", name=dir.name)
            if device:
                with open(Path(dir.path) / "data.yml") as data:
                    parameters = load(data)
                    device.update(**parameters)
                    with open(Path(dir.path) / dir.name) as f:
                        time = parameters["last_update"]
                        device.current_configuration = device.configurations[
                            time
                        ] = f.read()
        Session.commit()
        for pool in fetch_all("Pool"):
            if pool.device_current_configuration:
                pool.compute_pool()

    def get_git_content(self, app: Flask) -> None:
        for repository_type in ("configurations", "automation"):
            repo = getattr(self, f"git_{repository_type}")
            if not repo:
                continue
            local_path = app.path / "git" / repository_type
            for file in scandir(local_path):
                if file.name == ".gitkeep":
                    remove(file)
            try:
                Repo.clone_from(repo, local_path)
                if repository_type == "configurations":
                    self.update_database_configurations_from_git(app)
            except Exception as e:
                info(f"Cannot clone {repository_type} git repository ({str(e)})")
                try:
                    Repo(local_path).remotes.origin.pull()
                    if repository_type == "configurations":
                        self.update_database_configurations_from_git(app)
                except Exception as e:
                    info(f"Cannot pull {repository_type} git repository ({str(e)})")

    @property
    def gotty_range(self) -> int:
        return self.gotty_end_port - self.gotty_start_port

    def get_gotty_port(self) -> int:
        self.gotty_port_index += 1
        Session.commit()
        return self.gotty_start_port + self.gotty_port_index % self.gotty_range


class User(AbstractBase, UserMixin):

    __tablename__ = type = "User"
    id = Column(Integer, primary_key=True)
    email = Column(String(SMALL_STRING_LENGTH))
    name = Column(String(SMALL_STRING_LENGTH), unique=True)
    permissions = Column(MutableList.as_mutable(PickleType), default=[])
    pools = relationship("Pool", secondary=pool_user_table, back_populates="users")
    password = Column(String(SMALL_STRING_LENGTH))

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

    def generate_row(self, table: str) -> List[str]:
        return [
            f"""<button type="button" class="btn btn-primary btn-xs"
            onclick="showTypePanel('user', '{self.id}')">Edit</button>""",
            f"""<button type="button" class="btn btn-primary btn-xs"
            onclick="showTypePanel('user', '{self.id}', true)">
            Duplicate</button>""",
            f"""<button type="button" class="btn btn-danger btn-xs"
            onclick="showDeletionPanel('user', '{self.id}', '{self.name}')">
            Delete</button>""",
        ]

    @property
    def is_admin(self) -> bool:
        return "Admin" in self.permissions

    def allowed(self, permission: str) -> bool:
        return self.is_admin or permission in self.permissions
