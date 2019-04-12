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

from eNMS.associations import pool_user_table
from eNMS.functions import fetch, fetch_all
from eNMS.models import Base
from eNMS.extensions import db


class User(Base, UserMixin):

    __tablename__ = type = "User"
    id = Column(Integer, primary_key=True)
    email = Column(String(255))
    jobs = relationship("Job", back_populates="creator")
    name = Column(String(255), unique=True)
    permissions = Column(MutableList.as_mutable(PickleType), default=[])
    pools = relationship("Pool", secondary=pool_user_table, back_populates="users")
    password = Column(String(255))

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

    def generate_row(self, table: str) -> List[str]:
        return [
            f"""<button type="button" class="btn btn-primary btn-xs"
            onclick="showTypeModal('user', '{self.id}')">Edit</button>""",
            f"""<button type="button" class="btn btn-primary btn-xs"
            onclick="showTypeModal('user', '{self.id}', true)">
            Duplicate</button>""",
            f"""<button type="button" class="btn btn-danger btn-xs"
            onclick="confirmDeletion('user', '{self.id}')">Delete</button>""",
        ]

    @property
    def is_admin(self) -> bool:
        return "Admin" in self.permissions

    def allowed(self, permission: str) -> bool:
        return self.is_admin or permission in self.permissions


class Instance(Base):

    __tablename__ = type = "Instance"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True)
    description = Column(String(255))
    ip_address = Column(String(255))
    weight = Column(Integer, default=1)
    status = Column(String(255), default="down")
    cpu_load = Column(Float)

    def generate_row(self, table: str) -> List[str]:
        return [
            f"""<button type="button" class="btn btn-primary btn-xs"
            onclick="showTypeModal('instance', '{self.id}')">Edit</button>""",
            f"""<button type="button" class="btn btn-primary btn-xs"
            onclick="showTypeModal('instance', '{self.id}', true)">
            Duplicate</button>""",
            f"""<button type="button" class="btn btn-danger btn-xs"
            onclick="confirmDeletion('instance', '{self.id}')">
            Delete</button>""",
        ]


class Parameters(Base):

    __tablename__ = type = "Parameters"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), default="default", unique=True)
    cluster_scan_subnet = Column(String(255))
    cluster_scan_protocol = Column(String(255))
    cluster_scan_timeout = Column(Float)
    default_longitude = Column(Float)
    default_latitude = Column(Float)
    default_zoom_level = Column(Integer)
    default_view = Column(String(255))
    default_marker = Column(String(255))
    git_configurations = Column(String(255))
    git_automation = Column(String(255))
    gotty_start_port = Column(Integer)
    gotty_end_port = Column(Integer)
    gotty_port_index = Column(Integer, default=-1)
    opennms_rest_api = Column(
        String(255), default="https://demo.opennms.org/opennms/rest"
    )
    opennms_devices = Column(
        String(255), default="https://demo.opennms.org/opennms/rest/nodes"
    )
    opennms_login = Column(String(255), default="demo")
    mail_sender = Column(String(255))
    mail_recipients = Column(String(255))
    mattermost_url = Column(String(255))
    mattermost_channel = Column(String(255))
    mattermost_verify_certificate = Column(Boolean)
    slack_token = Column(String(255))
    slack_channel = Column(String(255))

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
        db.session.commit()
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

    def trigger_active_parameters(self, app: Flask) -> None:
        self.get_git_content(app)

    @property
    def gotty_range(self) -> int:
        return self.gotty_end_port - self.gotty_start_port

    def get_gotty_port(self) -> int:
        self.gotty_port_index += 1
        db.session.commit()
        return self.gotty_start_port + self.gotty_port_index % self.gotty_range
