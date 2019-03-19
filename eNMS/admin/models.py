from datetime import datetime
from flask import Flask
from flask_login import UserMixin
from git import Repo
from logging import info
from os import scandir, remove
from sqlalchemy import Boolean, Column, Float, Integer, PickleType, String
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.orm import relationship
from typing import Any

from eNMS.base.associations import pool_user_table
from eNMS.base.functions import fetch, fetch_all
from eNMS.base.models import Base
from eNMS.extensions import db


class User(Base, UserMixin):

    __tablename__ = type = "User"
    id = Column(Integer, primary_key=True)
    email = Column(String)
    jobs = relationship("Job", back_populates="creator")
    name = Column(String, unique=True)
    permissions = Column(MutableList.as_mutable(PickleType), default=[])
    pools = relationship("Pool", secondary=pool_user_table, back_populates="users")
    password = Column(String)

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

    @property
    def is_admin(self) -> bool:
        return "Admin" in self.permissions

    def allowed(self, permission: str) -> bool:
        return self.is_admin or permission in self.permissions


class Instance(Base):

    __tablename__ = type = "Instance"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    description = Column(String)
    ip_address = Column(String)
    weight = Column(Integer, default=1)
    status = Column(String, default="down")
    cpu_load = Column(Float)


class Parameters(Base):

    __tablename__ = type = "Parameters"
    id = Column(Integer, primary_key=True)
    name = Column(String, default="default", unique=True)
    cluster_scan_subnet = Column(String)
    cluster_scan_protocol = Column(String)
    cluster_scan_timeout = Column(Float)
    default_longitude = Column(Float)
    default_latitude = Column(Float)
    default_zoom_level = Column(Integer)
    git_configurations = Column(String)
    git_automation = Column(String)
    gotty_start_port = Column(Integer)
    gotty_end_port = Column(Integer)
    gotty_port_index = Column(Integer, default=-1)
    opennms_rest_api = Column(String, default="https://demo.opennms.org/opennms/rest")
    opennms_devices = Column(
        String, default="https://demo.opennms.org/opennms/rest/nodes"
    )
    opennms_login = Column(String, default="demo")
    mail_sender = Column(String)
    mail_recipients = Column(String)
    mattermost_url = Column(String)
    mattermost_channel = Column(String)
    mattermost_verify_certificate = Column(Boolean)
    slack_token = Column(String)
    slack_channel = Column(String)

    def update(self, **kwargs: Any) -> None:
        self.gotty_port_index = -1
        super().update(**kwargs)

    def update_database_configurations_from_git(self, app: Flask) -> None:
        for file in scandir(app.path / "git" / "configurations"):
            device = fetch("Device", name=file.name)
            if device:
                time = max(device.configurations, default=datetime.now())
                with open(file) as f:
                    device.current_configurations = device.configurations[
                        time
                    ] = f.read()
        db.session.commit()

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
            except Exception as e:
                info(f"Cannot clone {repository_type} git repository ({str(e)})")
                try:
                    Repo(local_path).remotes.origin.pull()
                    if repository_type == "configurations":
                        self.update_database_configurations_from_git(app)
                        for pool in fetch_all("Pool"):
                            if pool.device_current_configuration:
                                pool.compute_pool()
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
