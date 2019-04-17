from flask import Flask
from flask_login import UserMixin
from git import Repo
from logging import info
from os import scandir, remove
from pathlib import Path
from re import search
from sqlalchemy import Boolean, Column, Float, Integer, PickleType, String
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.orm import relationship
from socketserver import BaseRequestHandler, UDPServer
from threading import Thread
from typing import Any, List
from yaml import load

from eNMS.extensions import controller, db
from eNMS.functions import add_classes, fetch, fetch_all
from eNMS.associations import log_rule_log_table, pool_user_table
from eNMS.automation.models import LogRule
from eNMS.models.base_models import Base


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
            onclick="showTypePanel('user', '{self.id}')">Edit</button>""",
            f"""<button type="button" class="btn btn-primary btn-xs"
            onclick="showTypePanel('user', '{self.id}', true)">
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
            onclick="showTypePanel('instance', '{self.id}')">Edit</button>""",
            f"""<button type="button" class="btn btn-primary btn-xs"
            onclick="showTypePanel('instance', '{self.id}', true)">
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


class Log(Base):

    __tablename__ = type = "Log"
    id = Column(Integer, primary_key=True)
    source_ip = Column(String(255))
    content = Column(String(255))
    log_rules = relationship(
        "LogRule", secondary=log_rule_log_table, back_populates="logs"
    )

    def generate_row(self, table: str) -> List[str]:
        return [
            f"""<button type="button" class="btn btn-danger btn-xs"
            onclick="deleteInstance('Log', '{self.id}')">Delete</button>"""
        ]

    def __repr__(self) -> str:
        return self.content


class SyslogUDPHandler(BaseRequestHandler):
    def handle(self) -> None:
        with controller.app.app_context():
            data = str(bytes.decode(self.request[0].strip()))
            source, _ = self.client_address
            log_rules = []
            for log_rule in LogRule.query.all():
                source_match = (
                    search(log_rule.source_ip, source)
                    if log_rule.source_ip_regex
                    else log_rule.source_ip in source
                )
                content_match = (
                    search(log_rule.content, data)
                    if log_rule.content_regex
                    else log_rule.content in data
                )
                if source_match and content_match:
                    log_rules.append(log_rule)
                    for job in log_rule.jobs:
                        job.try_run()
            if log_rules:
                log = Log(**{"source": source, "date": data, "log_rules": log_rules})
                db.session.add(log)
                db.session.commit()


class SyslogServer(Base):

    __tablename__ = type = "SyslogServer"
    id = Column(Integer, primary_key=True)
    ip_address = Column(String(255))
    port = Column(Integer)

    def __init__(self, ip_address: str, port: int) -> None:
        self.ip_address = ip_address
        self.port = port
        self.start()

    def __repr__(self) -> str:
        return self.ip_address

    def start(self) -> None:
        UDPServer.allow_reuse_address = True
        self.server = UDPServer((self.ip_address, self.port), SyslogUDPHandler)
        th = Thread(target=self.server.serve_forever)
        th.daemon = True
        th.start()


add_classes(Log)
