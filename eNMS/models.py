from apscheduler.triggers.cron import CronTrigger
from copy import deepcopy
from datetime import datetime
from flask import Flask
from flask_login import current_user as user, UserMixin
from git import Repo
from json import dumps, loads
from logging import info
from multiprocessing.pool import ThreadPool
from napalm import get_network_driver
from napalm.base.base import NetworkDriver
from netmiko import ConnectHandler
from os import environ, scandir, remove
from paramiko import SSHClient
from pathlib import Path
from re import compile, search
from scp import SCPClient
from sqlalchemy import (
    Boolean,
    case,
    Column,
    Float,
    ForeignKey,
    Integer,
    PickleType,
    String,
    Table,
    Text,
)
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.ext.mutable import MutableList, MutableDict
from sqlalchemy.orm import backref, relationship
from socketserver import BaseRequestHandler, UDPServer
from threading import Thread
from time import sleep
from traceback import format_exc
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from xmltodict import parse
from yaml import load

from eNMS.extensions import controller, db, scheduler, USE_VAULT, vault_client
from eNMS.functions import (
    classes,
    service_classes,
    fetch,
    fetch_all,
    objectify,
    session_scope,
)
from eNMS.helpers import scheduler_job
from eNMS.properties import (
    cls_to_properties,
    custom_properties,
    dont_migrate,
    property_types,
    boolean_properties,
    pool_link_properties,
    pool_device_properties,
    relationships as rel,
    private_properties,
    sql_types,
)


def register_class(*args, **kwargs):
    cls = type(*args, **kwargs)
    if classes.get("Service") and issubclass(cls, classes["Service"]):
        service_classes[cls.__tablename__] = cls
    classes[cls.__tablename__] = cls
    return cls


class Base(db.Model):

    __abstract__ = True

    def __init__(self, **kwargs: Any) -> None:
        self.update(**kwargs)

    def __lt__(self, other: db.Model) -> bool:
        return True

    def __repr__(self) -> str:
        return self.name

    def __getattribute__(self, property: str) -> Any:
        if property in private_properties and USE_VAULT:
            path = f"secret/data/{self.__tablename__}/{self.name}/{property}"
            data = vault_client.read(path)
            return data["data"]["data"][property] if data else ""
        else:
            return super().__getattribute__(property)

    def __setattr__(self, property: str, value: Any) -> None:
        if property in private_properties and USE_VAULT:
            if not value:
                return
            vault_client.write(
                f"secret/data/{self.__tablename__}/{self.name}/{property}",
                data={property: value},
            )
        else:
            super().__setattr__(property, value)

    def update(self, **kwargs: Any) -> None:
        serial = rel.get(self.__tablename__, rel["Service"])
        for property, value in kwargs.items():
            property_type = property_types.get(property, None)
            if property in serial:
                value = fetch(serial[property], id=value)
            elif property[:-1] in serial:
                value = objectify(serial[property[:-1]], value)
            elif property in boolean_properties:
                value = kwargs[property] not in (None, False)
            elif "regex" in property:
                value = property in kwargs
            elif property_type == "dict" and type(value) == str:
                value = loads(value) if value else {}
            elif property_type in ["float", "int"]:
                default_value = getattr(self.__table__.c, property).default
                if default_value and not value:
                    value = default_value.arg
                value = {"float": float, "int": int}[property_type](value or 0)
            setattr(self, property, value)

    def get_properties(self) -> dict:
        result = {}
        for property in cls_to_properties[self.type]:
            if property in private_properties:
                continue
            try:
                dumps(getattr(self, property))
                result[property] = getattr(self, property)
            except TypeError:
                result[property] = str(getattr(self, property))
        return result

    def get_export_properties(self) -> dict:
        result = {}
        for property in cls_to_properties[self.type]:
            value = getattr(self, property)
            if not value or property in private_properties:
                continue
            try:
                dumps(value)
            except TypeError:
                continue
            if isinstance(value, MutableList):
                value = list(value)
            if isinstance(value, MutableDict):
                value = dict(value)
            result[property] = value
        return result

    def to_dict(self, export: bool = False) -> dict:
        properties = self.get_export_properties() if export else self.get_properties()
        no_migrate = dont_migrate.get(self.type, dont_migrate["Service"])
        for property in rel.get(self.type, rel["Service"]):
            if export and property in no_migrate:
                continue
            if hasattr(self, property):
                if hasattr(getattr(self, property), "get_properties"):
                    properties[property] = (
                        getattr(self, property).id
                        if export
                        else getattr(self, property).get_properties()
                    )
            if hasattr(self, f"{property}s"):
                properties[f"{property}s"] = [
                    obj.id if export else obj.get_properties()
                    for obj in getattr(self, f"{property}s")
                ]
        if export:
            for property in no_migrate:
                properties.pop(property, None)
        return properties

    @classmethod
    def visible(cls) -> List:
        if cls.__tablename__ == "Pool" and user.pools:
            return user.pools
        elif cls.__tablename__ in ("Device", "Link") and user.pools:
            objects: set = set()
            for pool in user.pools:
                objects |= set(getattr(pool, f"{cls.class_type}s"))
            return list(objects)
        else:
            return cls.query.all()

    @property
    def serialized(self) -> dict:
        return self.to_dict()

    @classmethod
    def export(cls: db.Model) -> List[dict]:
        return [obj.to_dict(export=True) for obj in cls.visible()]

    @classmethod
    def choices(cls: db.Model) -> List[Tuple[int, str]]:
        return [(obj.id, str(obj)) for obj in cls.visible()]

    @classmethod
    def serialize(cls: db.Model) -> List[dict]:
        return [obj.serialized for obj in cls.visible()]


job_device_table: Table = Table(
    "job_device_association",
    Base.metadata,
    Column("device_id", Integer, ForeignKey("Device.id")),
    Column("job_id", Integer, ForeignKey("Job.id")),
)

job_pool_table: Table = Table(
    "job_pool_association",
    Base.metadata,
    Column("pool_id", Integer, ForeignKey("Pool.id")),
    Column("job_id", Integer, ForeignKey("Job.id")),
)

log_rule_log_table: Table = Table(
    "log_rule_log_association",
    Base.metadata,
    Column("log_id", Integer, ForeignKey("Log.id")),
    Column("log_rule_id", Integer, ForeignKey("LogRule.id")),
)

job_log_rule_table: Table = Table(
    "job_log_rule_association",
    Base.metadata,
    Column("job_id", Integer, ForeignKey("Job.id")),
    Column("log_rule_id", Integer, ForeignKey("LogRule.id")),
)

job_workflow_table: Table = Table(
    "job_workflow_association",
    Base.metadata,
    Column("job_id", Integer, ForeignKey("Job.id")),
    Column("workflow_id", Integer, ForeignKey("Workflow.id")),
)

pool_device_table: Table = Table(
    "pool_device_association",
    Base.metadata,
    Column("pool_id", Integer, ForeignKey("Pool.id")),
    Column("device_id", Integer, ForeignKey("Device.id")),
)

pool_link_table: Table = Table(
    "pool_link_association",
    Base.metadata,
    Column("pool_id", Integer, ForeignKey("Pool.id")),
    Column("link_id", Integer, ForeignKey("Link.id")),
)

pool_user_table: Table = Table(
    "pool_user_association",
    Base.metadata,
    Column("pool_id", Integer, ForeignKey("Pool.id")),
    Column("user_id", Integer, ForeignKey("User.id")),
)


class User(Base, UserMixin, metaclass=register_class):

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
            onclick="showDeletionPanel('user', '{self.id}')">Delete</button>""",
        ]

    @property
    def is_admin(self) -> bool:
        return "Admin" in self.permissions

    def allowed(self, permission: str) -> bool:
        return self.is_admin or permission in self.permissions


class Instance(Base, metaclass=register_class):

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
            onclick="showDeletionPanel('instance', '{self.id}')">
            Delete</button>""",
        ]


class Parameters(Base, metaclass=register_class):

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


class Log(Base, metaclass=register_class):

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


class SyslogServer(Base, metaclass=register_class):

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


class Object(Base, metaclass=register_class):

    __tablename__ = "Object"
    type = Column(String(255))
    __mapper_args__ = {"polymorphic_identity": "Object", "polymorphic_on": type}
    id = Column(Integer, primary_key=True)
    hidden = Column(Boolean, default=False)
    name = Column(String(255), unique=True)
    subtype = Column(String(255))
    description = Column(String(255))
    model = Column(String(255))
    location = Column(String(255))
    vendor = Column(String(255))


CustomDevice: Any = (
    type(
        "CustomDevice",
        (Object,),
        {
            "__tablename__": "CustomDevice",
            "__mapper_args__": {"polymorphic_identity": "CustomDevice"},
            "id": Column(Integer, ForeignKey("Object.id"), primary_key=True),
            **{
                property: Column(sql_types[values["type"]], default=values["default"])
                for property, values in custom_properties.items()
            },
        },
    )
    if custom_properties
    else Object
)


class Device(CustomDevice, metaclass=register_class):

    __tablename__ = "Device"
    __mapper_args__ = {"polymorphic_identity": "Device"}
    class_type = "device"
    id = Column(Integer, ForeignKey(CustomDevice.id), primary_key=True)
    operating_system = Column(String(255))
    os_version = Column(String(255))
    ip_address = Column(String(255))
    longitude = Column(Float)
    latitude = Column(Float)
    port = Column(Integer, default=22)
    username = Column(String(255))
    password = Column(String(255))
    enable_password = Column(String(255))
    netmiko_driver = Column(String(255))
    napalm_driver = Column(String(255))
    configurations = Column(MutableDict.as_mutable(PickleType), default={})
    current_configuration = Column(Text)
    last_failure = Column(String(255), default="Never")
    last_status = Column(String(255), default="Never")
    last_update = Column(String(255), default="Never")
    last_runtime = Column(Float, default=0.0)
    jobs = relationship("Job", secondary=job_device_table, back_populates="devices")
    pools = relationship("Pool", secondary=pool_device_table, back_populates="devices")

    def update(self, **kwargs: Any) -> None:
        super().update(**kwargs)
        if kwargs.get("dont_update_pools", False):
            return
        for pool in fetch_all("Pool"):
            if pool.never_update:
                continue
            if pool.object_match(self):
                pool.devices.append(self)
            elif self in pool.devices:
                pool.devices.remove(self)

    def generate_row(self, table: str) -> List[str]:
        if table == "device":
            return [
                f"""<button type="button" class="btn btn-info btn-xs"
                onclick="showAutomationPanel('{self.id}')">Automation</button>""",
                f"""<button type="button" class="btn btn-success btn-xs"
                onclick="showConnectionPanel('{self.id}')">Connect</button>""",
                f"""<button type="button" class="btn btn-primary btn-xs"
                onclick="showTypePanel('device', '{self.id}')">Edit</button>""",
                f"""<button type="button" class="btn btn-primary btn-xs"
                onclick="showTypePanel('device', '{self.id}', true)">Duplicate</button>""",
                f"""<button type="button" class="btn btn-danger btn-xs"
                onclick="showDeletionPanel('device', '{self.id}')">Delete</button>""",
            ]
        else:
            return [
                f"""<button type="button" class="btn btn-primary btn-xs"
                onclick="showConfigurationPanel('{self.id}')">Configuration</button>"""
                if self.configurations
                else "",
                f"""<label class="btn btn-default btn-xs btn-file"
                style="width:100%;"><a href="download_configuration/{self.name}">
                Download</a></label>"""
                if self.configurations
                else "",
                f"""<button type="button" class="btn btn-primary btn-xs"
                onclick="showTypePanel('device', '{self.id}')">Edit</button>""",
            ]

    def __repr__(self) -> str:
        return f"{self.name} ({self.model})"


class Link(Object, metaclass=register_class):

    __tablename__ = "Link"
    __mapper_args__ = {"polymorphic_identity": "Link"}
    class_type = "link"
    id = Column(Integer, ForeignKey("Object.id"), primary_key=True)
    source_id = Column(Integer, ForeignKey("Device.id"))
    destination_id = Column(Integer, ForeignKey("Device.id"))
    source = relationship(
        Device,
        primaryjoin=source_id == Device.id,
        backref=backref("source", cascade="all, delete-orphan"),
    )
    source_name = association_proxy("source", "name")
    destination = relationship(
        Device,
        primaryjoin=destination_id == Device.id,
        backref=backref("destination", cascade="all, delete-orphan"),
    )
    destination_name = association_proxy("destination", "name")
    pools = relationship("Pool", secondary=pool_link_table, back_populates="links")

    def __init__(self, **kwargs: Any) -> None:
        self.update(**kwargs)

    @property
    def view_properties(self) -> Dict[str, Any]:
        node_properties = ("id", "longitude", "latitude")
        return {
            **{
                property: getattr(self, property)
                for property in ("id", "name", "subtype")
            },
            **{
                f"source_{property}": getattr(self.source, property)
                for property in node_properties
            },
            **{
                f"destination_{property}": getattr(self.destination, property)
                for property in node_properties
            },
        }

    def update(self, **kwargs: Any) -> None:
        if "source_name" in kwargs:
            kwargs["source"] = fetch("Device", name=kwargs.pop("source_name")).id
            kwargs["destination"] = fetch(
                "Device", name=kwargs.pop("destination_name")
            ).id
        kwargs.update(
            {"source_id": kwargs["source"], "destination_id": kwargs["destination"]}
        )
        super().update(**kwargs)
        for pool in fetch_all("Pool"):
            if pool.never_update:
                continue
            if pool.object_match(self):
                pool.links.append(self)
            elif self in pool.links:
                pool.links.remove(self)

    def generate_row(self, table: str) -> List[str]:
        return [
            f"""<button type="button" class="btn btn-primary btn-xs"
            onclick="showTypePanel('link', '{self.id}')">Edit</button>""",
            f"""<button type="button" class="btn btn-primary btn-xs"
            onclick="showTypePanel('link', '{self.id}', true)">Duplicate
            </button>""",
            f"""<button type="button" class="btn btn-danger btn-xs"
            onclick="showDeletionPanel('link', '{self.id}')">Delete</button>""",
        ]


AbstractPool: Any = type(
    "AbstractPool",
    (Base,),
    {
        "__tablename__": "AbstractPool",
        "type": "AbstractPool",
        "__mapper_args__": {"polymorphic_identity": "AbstractPool"},
        "id": Column(Integer, primary_key=True),
        **{
            **{
                f"device_{property}": Column(String(255))
                for property in pool_device_properties
            },
            **{
                f"device_{property}_match": Column(String(255), default="inclusion")
                for property in pool_device_properties
            },
            **{
                f"link_{property}": Column(String(255))
                for property in pool_link_properties
            },
            **{
                f"link_{property}_match": Column(String(255), default="inclusion")
                for property in pool_link_properties
            },
        },
    },
)


class Pool(AbstractPool, metaclass=register_class):

    __tablename__ = type = "Pool"
    id = Column(Integer, ForeignKey("AbstractPool.id"), primary_key=True)
    name = Column(String(255), unique=True)
    description = Column(String(255))
    operator = Column(String(255), default="all")
    devices = relationship(
        "Device", secondary=pool_device_table, back_populates="pools"
    )
    links = relationship("Link", secondary=pool_link_table, back_populates="pools")
    latitude = Column(Float)
    longitude = Column(Float)
    jobs = relationship("Job", secondary=job_pool_table, back_populates="pools")
    users = relationship("User", secondary=pool_user_table, back_populates="pools")
    never_update = Column(Boolean, default=False)

    def update(self, **kwargs: Any) -> None:
        super().update(**kwargs)
        self.compute_pool()

    def generate_row(self, table: str) -> List[str]:
        return [
            f"""<button type="button" class="btn btn-info btn-xs"
            onclick="showPoolView('{self.id}')">
            Visualize</button>""",
            f"""<button type="button" class="btn btn-primary btn-xs"
            onclick="showTypePanel('pool', '{self.id}')">
            Edit properties</button>""",
            f"""<button type="button" class="btn btn-primary btn-xs"
            onclick="updatePool('{self.id}')">Update</button>""",
            f"""<button type="button" class="btn btn-primary btn-xs"
            onclick="showTypePanel('pool', '{self.id}', true)">
            Duplicate</button>""",
            f"""<button type="button" class="btn btn-primary btn-xs"
            onclick="showPoolObjectsPanel('{self.id}')">Edit objects</button>""",
            f"""<button type="button" class="btn btn-danger btn-xs"
            onclick="showDeletionPanel('pool', '{self.id}')">Delete</button>""",
        ]

    @property
    def object_number(self) -> str:
        return f"{len(self.devices)} devices - {len(self.links)} links"

    def property_match(self, obj: Union[Device, Link], property: str) -> bool:
        pool_value = getattr(self, f"{obj.class_type}_{property}")
        object_value = str(getattr(obj, property))
        match = getattr(self, f"{obj.class_type}_{property}_match")
        if not pool_value:
            return True
        elif match == "inclusion":
            return pool_value in object_value
        elif match == "equality":
            return pool_value == object_value
        else:
            return bool(search(pool_value, object_value))

    def object_match(self, obj: Union[Device, Link]) -> bool:
        properties = (
            pool_device_properties
            if obj.class_type == "device"
            else pool_link_properties
        )
        operator = all if self.operator == "all" else any
        return operator(self.property_match(obj, property) for property in properties)

    def compute_pool(self) -> None:
        if self.never_update:
            return
        self.devices = list(filter(self.object_match, Device.query.all()))
        self.links = list(filter(self.object_match, Link.query.all()))


class Job(Base, metaclass=register_class):

    __tablename__ = "Job"
    type = Column(String(255))
    __mapper_args__ = {"polymorphic_identity": "Job", "polymorphic_on": type}
    id = Column(Integer, primary_key=True)
    hidden = Column(Boolean, default=False)
    name = Column(String(255), unique=True)
    description = Column(String(255))
    multiprocessing = Column(Boolean, default=False)
    max_processes = Column(Integer, default=5)
    number_of_retries = Column(Integer, default=0)
    time_between_retries = Column(Integer, default=10)
    positions = Column(MutableDict.as_mutable(PickleType), default={})
    results = Column(MutableDict.as_mutable(PickleType), default={})
    is_running = Column(Boolean, default=False)
    number_of_targets = Column(Integer, default=0)
    completed = Column(Integer, default=0)
    failed = Column(Integer, default=0)
    state = Column(MutableDict.as_mutable(PickleType), default={})
    credentials = Column(String(255), default="device")
    tasks = relationship("Task", back_populates="job", cascade="all,delete")
    vendor = Column(String(255))
    operating_system = Column(String(255))
    waiting_time = Column(Integer, default=0)
    creator_id = Column(Integer, ForeignKey("User.id"))
    creator = relationship("User", back_populates="jobs")
    creator_name = association_proxy("creator", "name")
    push_to_git = Column(Boolean, default=False)
    workflows = relationship(
        "Workflow", secondary=job_workflow_table, back_populates="jobs"
    )
    devices = relationship("Device", secondary=job_device_table, back_populates="jobs")
    pools = relationship("Pool", secondary=job_pool_table, back_populates="jobs")
    log_rules = relationship(
        "LogRule", secondary=job_log_rule_table, back_populates="jobs"
    )
    send_notification = Column(Boolean, default=False)
    send_notification_method = Column(String(255), default="mail_feedback_notification")
    display_only_failed_nodes = Column(Boolean, default=True)
    mail_recipient = Column(String(255), default="")
    logs = Column(MutableList.as_mutable(PickleType), default=[])

    @hybrid_property
    def status(self) -> str:
        return "Running" if self.is_running else "Idle"

    @status.expression  # type: ignore
    def status(cls) -> str:  # noqa: N805
        return case([(cls.is_running, "Running")], else_="Idle")

    @property
    def progress(self) -> str:
        if self.is_running:
            return f"{self.completed}/{self.number_of_targets} ({self.failed} failed)"
        else:
            return "N/A"

    def compute_targets(self) -> Set["Device"]:
        targets = set(self.devices)
        for pool in self.pools:
            targets |= set(pool.devices)
        self.number_of_targets = len(targets)
        db.session.commit()
        return targets

    def job_sources(self, workflow: "Workflow", subtype: str = "all") -> List["Job"]:
        return [
            x.source
            for x in self.sources
            if (subtype == "all" or x.subtype == subtype) and x.workflow == workflow
        ]

    def job_successors(self, workflow: "Workflow", subtype: str = "all") -> List["Job"]:
        return [
            x.destination
            for x in self.destinations
            if (subtype == "all" or x.subtype == subtype) and x.workflow == workflow
        ]

    def build_notification(self, results: dict, now: str) -> str:
        summary = [
            f"Job: {self.name} ({self.type})",
            f"Runtime: {now}",
            f'Status: {"PASS" if results["results"]["success"] else "FAILED"}',
        ]
        if "devices" in results["results"] and not results["results"]["success"]:
            failed = "\n".join(
                device
                for device, device_results in results["results"]["devices"].items()
                if not device_results["success"]
            )
            summary.append(f"FAILED\n{failed}")
            if not self.display_only_failed_nodes:
                passed = "\n".join(
                    device
                    for device, device_results in results["results"]["devices"].items()
                    if device_results["success"]
                )
                summary.append(f"\n\nPASS:\n{passed}")
        server_url = environ.get("ENMS_SERVER_ADDR", "http://SERVER_IP")
        results_url = f"{server_url}/automation/results/{self.id}/{now}"
        summary.append(f"Results: {results_url}")
        return "\n\n".join(summary)

    def notify(self, results: dict, time: str) -> None:
        fetch("Job", name=self.send_notification_method).try_run(
            {
                "job": self.serialized,
                "results": self.results,
                "runtime": time,
                "result": results["results"]["success"],
                "content": self.build_notification(results, time),
            }
        )

    def try_run(
        self,
        payload: Optional[dict] = None,
        targets: Optional[Set["Device"]] = None,
        workflow: Optional["Workflow"] = None,
    ) -> Tuple[dict, str]:
        self.is_running, self.state, self.logs = True, {}, []
        db.session.commit()
        results: dict = {"results": {}}
        if not payload:
            payload = {}
        job_from_workflow_targets = bool(workflow and targets)
        if not targets and getattr(self, "use_workflow_targets", True):
            targets = self.compute_targets()
        has_targets = bool(targets)
        if has_targets and not job_from_workflow_targets:
            results["results"]["devices"] = {}
        now = str(datetime.now()).replace(" ", "-")
        logs = workflow.logs if workflow else self.logs
        logs.append(f"{self.type} {self.name}: Starting.")
        for i in range(self.number_of_retries + 1):
            self.completed = self.failed = 0
            db.session.commit()
            logs.append(f"Running {self.type} {self.name} (attempt n°{i + 1})")
            attempt = self.run(payload, job_from_workflow_targets, targets, workflow)
            if has_targets and not job_from_workflow_targets:
                assert targets is not None
                for device in set(targets):
                    if not attempt["devices"][device.name]["success"]:
                        continue
                    results["results"]["devices"][device.name] = attempt["devices"][
                        device.name
                    ]
                    targets.remove(device)
                if not targets:
                    results["results"]["success"] = True
                    break
                else:
                    if self.number_of_retries:
                        results[f"Attempts {i + 1}"] = attempt
                    if i != self.number_of_retries:
                        sleep(self.time_between_retries)
                    else:
                        results["results"]["success"] = False
                        for device in targets:
                            results["results"]["devices"][device.name] = attempt[
                                "devices"
                            ][device.name]
            else:
                if self.number_of_retries:
                    results[f"Attempts {i + 1}"] = attempt
                if attempt["success"] or i == self.number_of_retries:
                    results["results"] = attempt
                    break
                else:
                    sleep(self.time_between_retries)
        logs.append(f"{self.type} {self.name}: Finished.")
        self.results[now] = {**results, "logs": logs}
        self.is_running, self.state = False, {}
        self.completed = self.failed = 0
        db.session.commit()
        if not workflow and self.send_notification:
            self.notify(results, now)
        return results, now

    def get_results(
        self,
        payload: dict,
        device: Optional["Device"] = None,
        workflow: Optional["Workflow"] = None,
        threaded: bool = False,
    ) -> dict:
        logs = workflow.logs if workflow else self.logs
        try:
            if device:
                logs.append(f"Running {self.type} on {device.name}.")
                results = self.job(payload, device)
                success = "SUCCESS" if results["success"] else "FAILURE"
                logs.append(f"Finished running service on {device.name}. ({success})")
            else:
                results = self.job(payload)
        except Exception:
            if device:
                logs.append(f"Finished running service on {device.name}. (FAILURE)")
            results = {
                "success": False,
                "result": chr(10).join(format_exc().splitlines()),
            }
        self.completed += 1
        self.failed += 1 - results["success"]
        if not threaded:
            db.session.commit()
        return results

    def device_run(
        self, args: Tuple["Device", dict, dict, Optional["Workflow"]]
    ) -> None:
        with controller.app.app_context():
            with session_scope() as session:
                device, results, payload, workflow = args
                device_result = self.get_results(payload, device, workflow, True)
                session.merge(workflow or self)
                results["devices"][device.name] = device_result

    def run(
        self,
        payload: dict,
        job_from_workflow_targets: bool,
        targets: Optional[Set["Device"]] = None,
        workflow: Optional["Workflow"] = None,
    ) -> dict:
        if job_from_workflow_targets:
            assert targets is not None
            device, = targets
            return self.get_results(payload, device, workflow)
        elif targets:
            results: dict = {"devices": {}}
            if self.multiprocessing:
                processes = min(len(targets), self.max_processes)
                pool = ThreadPool(processes=processes)
                pool.map(
                    self.device_run,
                    [(device, results, payload, workflow) for device in targets],
                )
                pool.close()
                pool.join()
            else:
                results["devices"] = {
                    device.name: self.get_results(payload, device, workflow)
                    for device in targets
                }
            return results
        else:
            return self.get_results(payload)


class Service(Job, metaclass=register_class):

    __tablename__ = "Service"
    id = Column(Integer, ForeignKey("Job.id"), primary_key=True)
    __mapper_args__ = {"polymorphic_identity": "Service"}

    def generate_row(self, table: str) -> List[str]:
        return [
            f"""<button type="button" class="btn btn-info btn-xs"
            onclick="showLogs('{self.id}')"></i>Logs</a></button>""",
            f"""<button type="button" class="btn btn-info btn-xs"
            onclick="showResults('{self.id}')"></i>Results</a></button>""",
            f"""<button type="button" class="btn btn-success btn-xs"
            onclick="runJob('{self.id}')">Run</button>""",
            f"""<button type="button" class="btn btn-primary btn-xs"
            onclick="showTypePanel('service', '{self.id}')">Edit</button>""",
            f"""<button type="button" class="btn btn-primary btn-xs"
            onclick="showTypePanel('service', '{self.id}', true)">Duplicate</button>""",
            f"""<button type="button" class="btn btn-danger btn-xs"
            onclick="showDeletionPanel('service', '{self.id}')">
            Delete</button>""",
        ]

    def get_credentials(self, device: "Device") -> Tuple[str, str]:
        return (
            (self.creator.name, self.creator.password)
            if self.credentials == "user"
            else (device.username, device.password)
        )

    def netmiko_connection(self, device: "Device") -> ConnectHandler:
        username, password = self.get_credentials(device)
        return ConnectHandler(
            device_type=(
                device.netmiko_driver if self.use_device_driver else self.driver
            ),
            ip=device.ip_address,
            username=username,
            password=password,
            secret=device.enable_password,
            fast_cli=self.fast_cli,
            timeout=self.timeout,
            global_delay_factor=self.global_delay_factor,
        )

    def napalm_connection(self, device: "Device") -> NetworkDriver:
        username, password = self.get_credentials(device)
        optional_args = self.optional_args
        if not optional_args:
            optional_args = {}
        if "secret" not in optional_args:
            optional_args["secret"] = device.enable_password
        driver = get_network_driver(
            device.napalm_driver if self.use_device_driver else self.driver
        )
        return driver(
            hostname=device.ip_address,
            username=username,
            password=password,
            optional_args=optional_args,
        )

    def sub(self, data: str, variables: dict) -> str:
        r = compile("{{(.*?)}}")

        def replace_with_locals(match: Any) -> str:
            return str(eval(match.group()[2:-2], variables))

        return r.sub(replace_with_locals, data)

    def space_deleter(self, input: str) -> str:
        return "".join(input.split())

    def match_content(self, result: Any, match: str) -> bool:
        if getattr(self, "conversion_method", False):
            if self.conversion_method == "json":
                result = load(result)
            elif self.conversion_method == "xml":
                result = parse(result)
        if getattr(self, "validation_method", "text") == "text":
            result = str(result)
            if self.delete_spaces_before_matching:
                match, result = map(self.space_deleter, (match, result))
            success = (
                self.content_match_regex
                and bool(search(match, result))
                or match in result
                and not self.content_match_regex
            )
        else:
            success = self.match_dictionary(result)
        return success if not self.negative_logic else not success

    def match_dictionary(self, result: dict, match: Optional[dict] = None) -> bool:
        if self.validation_method == "dict_equal":
            return result == self.dict_match
        else:
            if match is None:
                match = deepcopy(self.dict_match)
            for k, v in result.items():
                if isinstance(v, dict):
                    self.match_dictionary(v, match)
                elif k in match and match[k] == v:
                    match.pop(k)
            return not match

    def transfer_file(
        self, ssh_client: SSHClient, files: List[Tuple[str, str]]
    ) -> None:
        if self.protocol == "sftp":
            sftp = ssh_client.open_sftp()
            for source, destination in files:
                getattr(sftp, self.direction)(source, destination)
            sftp.close()
        else:
            with SCPClient(ssh_client.get_transport()) as scp:
                for source, destination in files:
                    getattr(scp, self.direction)(source, destination)


class WorkflowEdge(Base, metaclass=register_class):

    __tablename__ = type = "WorkflowEdge"
    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    subtype = Column(String(255))
    source_id = Column(Integer, ForeignKey("Job.id"))
    source = relationship(
        "Job",
        primaryjoin="Job.id == WorkflowEdge.source_id",
        backref=backref("destinations", cascade="all, delete-orphan"),
        foreign_keys="WorkflowEdge.source_id",
    )
    destination_id = Column(Integer, ForeignKey("Job.id"))
    destination = relationship(
        "Job",
        primaryjoin="Job.id == WorkflowEdge.destination_id",
        backref=backref("sources", cascade="all, delete-orphan"),
        foreign_keys="WorkflowEdge.destination_id",
    )
    workflow_id = Column(Integer, ForeignKey("Workflow.id"))
    workflow = relationship(
        "Workflow", back_populates="edges", foreign_keys="WorkflowEdge.workflow_id"
    )


class Workflow(Job, metaclass=register_class):

    __tablename__ = "Workflow"
    __mapper_args__ = {"polymorphic_identity": "Workflow"}
    id = Column(Integer, ForeignKey("Job.id"), primary_key=True)
    use_workflow_targets = Column(Boolean, default=True)
    last_modified = Column(String(255))
    jobs = relationship("Job", secondary=job_workflow_table, back_populates="workflows")
    edges = relationship("WorkflowEdge", back_populates="workflow")

    def __init__(self, **kwargs: Any) -> None:
        end = fetch("Service", name="End")
        default = [fetch("Service", name="Start"), end]
        self.jobs.extend(default)
        super().__init__(**kwargs)
        if self.name not in end.positions:
            end.positions[self.name] = (500, 0)

    def generate_row(self, table: str) -> List[str]:
        return [
            f"""<button type="button" class="btn btn-info btn-xs"
            onclick="showLogs('{self.id}')"></i>Logs</a></button>""",
            f"""<button type="button" class="btn btn-info btn-xs"
            onclick="showResults('{self.id}')"></i>Results</a></button>""",
            f"""<button type="button" class="btn btn-success btn-xs"
            onclick="runJob('{self.id}')">Run</button>""",
            f"""<button type="button" class="btn btn-primary btn-xs"
            onclick="showTypePanel('workflow', '{self.id}')">
            Edit</button>""",
            f"""<button type="button" class="btn btn-primary btn-xs"
            onclick="showWorkflowModalDuplicate('{self.id}')">
            Duplicate</button>""",
            f"""<button type="button" class="btn btn-danger btn-xs"
            onclick="showDeletionPanel('workflow', '{self.id}')">
            Delete</button>""",
        ]

    def job(self, payload: dict, device: Optional["Device"] = None) -> dict:
        self.state = {"jobs": {}}
        if device:
            self.state["current_device"] = device.name
        db.session.commit()
        jobs: List[Job] = [self.jobs[0]]
        visited: Set = set()
        results: dict = {"success": False}
        while jobs:
            job = jobs.pop()
            if any(
                node not in visited for node in job.job_sources(self, "prerequisite")
            ):
                continue
            visited.add(job)
            self.state["current_job"] = job.get_properties()
            db.session.commit()
            log = f"Workflow {self.name}: job {job.name}"
            if device:
                log += f" on {device.name}"
            info(log)
            job_results, _ = job.try_run(
                results, {device} if device else None, workflow=self
            )
            success = job_results["results"]["success"]
            self.state["jobs"][job.id] = success
            db.session.commit()
            edge_type_to_follow = "success" if success else "failure"
            for successor in job.job_successors(self, edge_type_to_follow):
                if successor not in visited:
                    jobs.append(successor)
                if successor == self.jobs[1]:
                    results["success"] = True
            results[job.name] = job_results
            sleep(job.waiting_time)
        return results


class LogRule(Base, metaclass=register_class):

    __tablename__ = type = "LogRule"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True)
    source_ip = Column(String(255))
    source_ip_regex = Column(Boolean)
    content = Column(String(255))
    content_regex = Column(Boolean)
    logs = relationship("Log", secondary=log_rule_log_table, back_populates="log_rules")
    jobs = relationship("Job", secondary=job_log_rule_table, back_populates="log_rules")

    def generate_row(self, table: str) -> List[str]:
        return [
            f"""<button type="button" class="btn btn-info btn-xs"
            onclick="showTypePanel('logrule', '{self.id}')">
            Edit</button>""",
            f"""<button type="button" class="btn btn-danger btn-xs"
            onclick="deleteInstance('logrule', '{self.id}')">
            Delete</button>""",
        ]


class Task(Base, metaclass=register_class):

    __tablename__ = "Task"
    type = "Task"
    id = Column(Integer, primary_key=True)
    aps_job_id = Column(String(255))
    name = Column(String(255), unique=True)
    description = Column(String(255))
    creation_time = Column(String(255))
    scheduling_mode = Column(String(255), default="standard")
    periodic = Column(Boolean)
    frequency = Column(Integer)
    frequency_unit = Column(String(255), default="seconds")
    start_date = Column(String(255))
    end_date = Column(String(255))
    crontab_expression = Column(String(255))
    is_active = Column(Boolean, default=False)
    job_id = Column(Integer, ForeignKey("Job.id"))
    job = relationship("Job", back_populates="tasks")
    job_name = association_proxy("job", "name")

    def __init__(self, **kwargs: Any) -> None:
        super().update(**kwargs)
        self.creation_time = str(datetime.now())
        self.aps_job_id = kwargs.get("aps_job_id", self.creation_time)
        if self.is_active:
            self.schedule()

    def update(self, **kwargs: Any) -> None:
        super().update(**kwargs)
        if self.is_active:
            self.schedule()

    def generate_row(self, table: str) -> List[str]:
        status = "Pause" if self.is_active else "Resume"
        return [
            f"""<button id="pause-resume-{self.id}" type="button"
            class="btn btn-success btn-xs" onclick=
            "{status.lower()}Task('{self.id}')">{status}</button>""",
            f"""<button type="button" class="btn btn-primary btn-xs"
            onclick="showTypePanel('task', '{self.id}')">Edit</button>""",
            f"""<button type="button" class="btn btn-primary btn-xs"
            onclick="showTypePanel('task', '{self.id}', true)">
            Duplicate</button>""",
            f"""<button type="button" class="btn btn-danger btn-xs"
            onclick="showDeletionPanel('task', '{self.id}')">
            Delete</button>""",
        ]

    @hybrid_property
    def status(self) -> str:
        return "Active" if self.is_active else "Inactive"

    @status.expression  # type: ignore
    def status(cls) -> str:  # noqa: N805
        return case([(cls.is_active, "Active")], else_="Inactive")

    @property
    def next_run_time(self) -> Optional[str]:
        job = scheduler.get_job(self.aps_job_id)
        if job and job.next_run_time:
            return job.next_run_time.strftime("%Y-%m-%d %H:%M:%S")
        return None

    @property
    def time_before_next_run(self) -> Optional[str]:
        job = scheduler.get_job(self.aps_job_id)
        if job and job.next_run_time:
            delta = job.next_run_time.replace(tzinfo=None) - datetime.now()
            hours, remainder = divmod(delta.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            days = f"{delta.days} days, " if delta.days else ""
            return f"{days}{hours}h:{minutes}m:{seconds}s"
        return None

    def aps_conversion(self, date: str) -> str:
        dt: datetime = datetime.strptime(date, "%d/%m/%Y %H:%M:%S")
        return datetime.strftime(dt, "%Y-%m-%d %H:%M:%S")

    def aps_date(self, datetype: str) -> Optional[str]:
        date = getattr(self, datetype)
        return self.aps_conversion(date) if date else None

    def pause(self) -> None:
        scheduler.pause_job(self.aps_job_id)
        self.is_active = False
        db.session.commit()

    def resume(self) -> None:
        self.schedule()
        scheduler.resume_job(self.aps_job_id)
        self.is_active = True
        db.session.commit()

    def delete_task(self) -> None:
        if scheduler.get_job(self.aps_job_id):
            scheduler.remove_job(self.aps_job_id)
        db.session.commit()

    def kwargs(self) -> Tuple[dict, dict]:
        default = {
            "id": self.aps_job_id,
            "func": scheduler_job,
            "replace_existing": True,
            "args": [self.job.id, self.aps_job_id],
        }
        if self.scheduling_mode == "cron":
            self.periodic = True
            trigger = {"trigger": CronTrigger.from_crontab(self.crontab_expression)}
        elif self.frequency:
            self.periodic = True
            frequency_in_seconds = (
                int(self.frequency)
                * {"seconds": 1, "minutes": 60, "hours": 3600, "days": 86400}[
                    self.frequency_unit
                ]
            )
            trigger = {
                "trigger": "interval",
                "start_date": self.aps_date("start_date"),
                "end_date": self.aps_date("end_date"),
                "seconds": frequency_in_seconds,
            }
        else:
            self.periodic = False
            trigger = {"trigger": "date", "run_date": self.aps_date("start_date")}
        return default, trigger

    def schedule(self) -> None:
        default, trigger = self.kwargs()
        if not scheduler.get_job(self.aps_job_id):
            scheduler.add_job(**{**default, **trigger})
        else:
            scheduler.reschedule_job(default.pop("id"), **trigger)


classes = {}
for model in (
    Device,
    Instance,
    Job,
    Link,
    Log,
    LogRule,
    Parameters,
    Pool,
    Service,
    Task,
    User,
    Workflow,
    WorkflowEdge,
):
    classes.update({model.__tablename__: model, model.__tablename__.lower(): model})
