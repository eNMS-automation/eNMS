from builtins import __dict__ as builtins
from copy import deepcopy
from datetime import datetime
from functools import partial
from importlib import __import__ as importlib_import
from io import BytesIO, StringIO
from json import dump, load, loads
from json.decoder import JSONDecodeError
from multiprocessing.pool import ThreadPool
from napalm import get_network_driver
from netmiko import ConnectHandler
from os import getenv
from paramiko import RSAKey, SFTPClient
from re import compile, search
from requests import post
from scp import SCPClient
from sqlalchemy import Boolean, ForeignKey, Index, Integer, or_
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import aliased, relationship
from threading import Thread
from time import sleep
from traceback import format_exc
from warnings import warn
from xmltodict import parse
from xml.parsers.expat import ExpatError

try:
    from scrapli import Scrapli
except ImportError as exc:
    warn(f"Couldn't import scrapli module ({exc})")

try:
    from slackclient import SlackClient
except ImportError as exc:
    warn(f"Couldn't import slackclient module ({exc})")

from eNMS import app
from eNMS.automation import ServiceRun
from eNMS.database import db
from eNMS.models.base import AbstractBase
from eNMS.models import models
from eNMS.models.inventory import Device  # noqa: F401
from eNMS.models.scheduling import Task  # noqa: F401
from eNMS.models.administration import User  # noqa: F401


class Service(AbstractBase):

    __tablename__ = class_type = "service"
    pool_model = True
    type = db.Column(db.SmallString)
    __mapper_args__ = {"polymorphic_identity": "service", "polymorphic_on": type}
    id = db.Column(Integer, primary_key=True)
    name = db.Column(db.SmallString, unique=True)
    creator = db.Column(db.SmallString)
    access_groups = db.Column(db.LargeString)
    default_access = db.Column(db.SmallString)
    shared = db.Column(Boolean, default=False)
    scoped_name = db.Column(db.SmallString, index=True)
    last_modified = db.Column(db.TinyString, info={"log_change": False})
    description = db.Column(db.LargeString)
    number_of_retries = db.Column(Integer, default=0)
    time_between_retries = db.Column(Integer, default=10)
    max_number_of_retries = db.Column(Integer, default=100)
    credential_type = db.Column(db.SmallString, default="any")
    positions = db.Column(db.Dict, info={"log_change": False})
    disable_result_creation = db.Column(Boolean, default=False)
    tasks = relationship("Task", back_populates="service", cascade="all,delete")
    vendor = db.Column(db.SmallString)
    operating_system = db.Column(db.SmallString)
    waiting_time = db.Column(Integer, default=0)
    workflows = relationship(
        "Workflow", secondary=db.service_workflow_table, back_populates="services"
    )
    device_query = db.Column(db.LargeString)
    device_query_property = db.Column(db.SmallString, default="ip_address")
    target_devices = relationship(
        "Device",
        secondary=db.service_target_device_table,
        back_populates="target_services",
    )
    target_pools = relationship(
        "Pool", secondary=db.service_target_pool_table, back_populates="target_services"
    )
    pools = relationship(
        "Pool", secondary=db.pool_service_table, back_populates="services"
    )
    update_target_pools = db.Column(Boolean, default=False)
    update_pools_after_running = db.Column(Boolean, default=False)
    send_notification = db.Column(Boolean, default=False)
    send_notification_method = db.Column(db.TinyString, default="mail")
    notification_header = db.Column(db.LargeString)
    display_only_failed_nodes = db.Column(Boolean, default=True)
    include_device_results = db.Column(Boolean, default=True)
    include_link_in_summary = db.Column(Boolean, default=True)
    mail_recipient = db.Column(db.SmallString)
    reply_to = db.Column(db.SmallString)
    initial_payload = db.Column(db.Dict)
    skip = db.Column(db.Dict)
    skip_query = db.Column(db.LargeString)
    skip_value = db.Column(db.SmallString, default="True")
    iteration_values = db.Column(db.LargeString)
    iteration_variable_name = db.Column(db.SmallString, default="iteration_value")
    iteration_devices = db.Column(db.LargeString)
    iteration_devices_property = db.Column(db.TinyString, default="ip_address")
    preprocessing = db.Column(db.LargeString)
    postprocessing = db.Column(db.LargeString)
    postprocessing_mode = db.Column(db.TinyString, default="always")
    log_level = db.Column(Integer, default=1)
    runs = relationship(
        "Run",
        foreign_keys="[Run.service_id]",
        back_populates="service",
        cascade="all, delete-orphan",
    )
    logs = relationship(
        "ServiceLog",
        foreign_keys="[ServiceLog.service_id]",
        back_populates="service",
        cascade="all, delete-orphan",
    )
    maximum_runs = db.Column(Integer, default=1)
    multiprocessing = db.Column(Boolean, default=False)
    max_processes = db.Column(Integer, default=5)
    status = db.Column(db.TinyString, default="Idle")
    validation_condition = db.Column(db.TinyString, default="none")
    conversion_method = db.Column(db.TinyString, default="none")
    validation_method = db.Column(db.TinyString, default="text")
    content_match = db.Column(db.LargeString)
    content_match_regex = db.Column(Boolean, default=False)
    dict_match = db.Column(db.Dict)
    negative_logic = db.Column(Boolean, default=False)
    delete_spaces_before_matching = db.Column(Boolean, default=False)
    run_method = db.Column(db.TinyString, default="per_device")

    def __init__(self, **kwargs):
        kwargs.pop("status", None)
        super().__init__(**kwargs)
        if "name" not in kwargs:
            self.set_name()

    def update(self, **kwargs):
        if "scoped_name" in kwargs and kwargs.get("scoped_name") != self.scoped_name:
            self.set_name(kwargs["scoped_name"])
        if self.positions and "positions" in kwargs:
            kwargs["positions"] = {**self.positions, **kwargs["positions"]}
        super().update(**kwargs)

    @classmethod
    def filtering_constraints(cls, **kwargs):
        workflow_id, constraints = kwargs["form"].get("workflow-filtering"), []
        if workflow_id:
            constraints.extend(
                [
                    models["service"].workflows.any(
                        models["workflow"].id == int(workflow_id)
                    ),
                    ~or_(
                        models["service"].scoped_name == name
                        for name in ("Start", "End")
                    ),
                ]
            )
        elif kwargs["form"].get("parent-filtering", "true") == "true":
            constraints.append(~models["service"].workflows.any())
        return constraints

    def duplicate(self, workflow=None):
        for i in range(10):
            number = f" ({i})" if i else ""
            scoped_name = f"{self.scoped_name}{number}"
            name = f"[{workflow.name}] {scoped_name}" if workflow else scoped_name
            if not db.fetch("service", allow_none=True, name=name):
                service = super().duplicate(
                    name=name, scoped_name=scoped_name, shared=False, update_pools=True
                )
                break
        if workflow:
            workflow.services.append(service)
        return service

    @property
    def filename(self):
        return app.strip_all(self.name)

    @classmethod
    def rbac_filter(cls, query, mode, user):
        query = query.filter(cls.default_access != "admin")
        pool_alias = aliased(models["pool"])
        return query.filter(cls.default_access == "public").union(
            query.join(cls.pools)
            .join(models["access"], models["pool"].access)
            .join(pool_alias, models["access"].user_pools)
            .join(models["user"], pool_alias.users)
            .filter(models["access"].access_type.contains(mode))
            .filter(models["user"].name == user.name),
            query.filter(cls.creator == user.name),
        )

    def set_name(self, name=None):
        if self.shared:
            workflow = "[Shared] "
        elif not self.workflows:
            workflow = ""
        else:
            workflow = f"[{self.workflows[0].name}] "
        self.name = f"{workflow}{name or self.scoped_name}"

    def neighbors(self, workflow, direction, subtype):
        for edge in getattr(self, f"{direction}s"):
            if edge.subtype == subtype and edge.workflow == workflow:
                yield getattr(edge, direction), edge


class ConnectionService(Service):

    __tablename__ = "connection_service"
    id = db.Column(Integer, ForeignKey("service.id"), primary_key=True)
    parent_type = "service"
    credentials = db.Column(db.SmallString, default="device")
    custom_username = db.Column(db.SmallString)
    custom_password = db.Column(db.SmallString)
    start_new_connection = db.Column(Boolean, default=False)
    close_connection = db.Column(Boolean, default=False)
    __mapper_args__ = {"polymorphic_identity": "connection_service"}


class Result(AbstractBase):

    __tablename__ = type = "result"
    private = True
    log_change = False
    id = db.Column(Integer, primary_key=True)
    success = db.Column(Boolean, default=False)
    runtime = db.Column(db.TinyString)
    duration = db.Column(db.TinyString)
    result = db.Column(db.Dict)
    run_id = db.Column(Integer, ForeignKey("run.id", ondelete="cascade"))
    run = relationship("Run", back_populates="results", foreign_keys="Result.run_id")
    parent_runtime = db.Column(db.TinyString)
    parent_device_id = db.Column(Integer, ForeignKey("device.id"))
    parent_device = relationship("Device", uselist=False, foreign_keys=parent_device_id)
    parent_device_name = association_proxy("parent_device", "name")
    device_id = db.Column(Integer, ForeignKey("device.id"))
    device = relationship("Device", uselist=False, foreign_keys=device_id)
    device_name = association_proxy("device", "name")
    service_id = db.Column(Integer, ForeignKey("service.id"))
    service = relationship("Service", foreign_keys="Result.service_id")
    service_name = association_proxy(
        "service", "scoped_name", info={"name": "service_name"}
    )
    workflow_id = db.Column(Integer, ForeignKey("workflow.id", ondelete="cascade"))
    workflow = relationship("Workflow", foreign_keys="Result.workflow_id")
    workflow_name = association_proxy(
        "workflow", "scoped_name", info={"name": "workflow_name"}
    )

    def __getitem__(self, key):
        return self.result[key]

    def __init__(self, **kwargs):
        self.success = kwargs["result"]["success"]
        self.runtime = kwargs["result"]["runtime"]
        self.duration = kwargs["result"]["duration"]
        super().__init__(**kwargs)
        self.parent_runtime = self.run.parent_runtime

    def __repr__(self):
        return f"SERVICE '{self.service}' - DEVICE '{self.device} ({self.runtime})"

    @classmethod
    def filtering_constraints(cls, **kwargs):
        constraints = []
        if kwargs.get("rest_api_request", False):
            return []
        if kwargs.get("runtime"):
            constraints.append(models["result"].parent_runtime == kwargs["runtime"])
        return constraints


class ServiceLog(AbstractBase):

    __tablename__ = type = "service_log"
    private = True
    log_change = False
    id = db.Column(Integer, primary_key=True)
    content = db.Column(db.LargeString)
    runtime = db.Column(db.TinyString)
    service_id = db.Column(Integer, ForeignKey("service.id"))
    service = relationship("Service", foreign_keys="ServiceLog.service_id")

    def __repr__(self):
        return f"SERVICE '{self.service}' ({self.runtime})"


class Run(AbstractBase):

    __tablename__ = type = "run"
    __table_args__ = (
        Index("ix_run_parent_runtime_0", "parent_runtime", "runtime"),
        Index(
            "ix_run_start_service_id_0", "start_service_id", "parent_runtime", "runtime"
        ),
    )
    private = True
    id = db.Column(Integer, primary_key=True)
    restart_run_id = db.Column(Integer, ForeignKey("run.id"))
    restart_run = relationship("Run", uselist=False, foreign_keys=restart_run_id)
    start_services = db.Column(db.List)
    creator = db.Column(db.SmallString, default="")
    properties = db.Column(db.Dict)
    success = db.Column(Boolean, default=False)
    status = db.Column(db.TinyString, default="Running")
    runtime = db.Column(db.TinyString, index=True)
    duration = db.Column(db.TinyString)
    trigger = db.Column(db.TinyString, default="UI")
    parent_id = db.Column(Integer, ForeignKey("run.id", ondelete="cascade"))
    parent = relationship(
        "Run", remote_side=[id], foreign_keys="Run.parent_id", back_populates="children"
    )
    children = relationship("Run", foreign_keys="Run.parent_id")
    parent_runtime = db.Column(db.TinyString)
    path = db.Column(db.TinyString)
    parent_device_id = db.Column(Integer, ForeignKey("device.id"))
    parent_device = relationship("Device", foreign_keys="Run.parent_device_id")
    target_devices = relationship(
        "Device", secondary=db.run_device_table, back_populates="runs"
    )
    target_pools = relationship(
        "Pool", secondary=db.run_pool_table, back_populates="runs"
    )
    service_id = db.Column(Integer, ForeignKey("service.id"))
    service = relationship(
        "Service", back_populates="runs", foreign_keys="Run.service_id"
    )
    service_name = association_proxy(
        "service", "scoped_name", info={"name": "service_name"}
    )
    placeholder_id = db.Column(Integer, ForeignKey("service.id", ondelete="SET NULL"))
    placeholder = relationship("Service", foreign_keys="Run.placeholder_id")
    start_service_id = db.Column(Integer, ForeignKey("service.id", ondelete="SET NULL"))
    start_service = relationship("Service", foreign_keys="Run.start_service_id")
    start_service_name = association_proxy(
        "start_service", "scoped_name", info={"name": "start_service_name"}
    )
    workflow_id = db.Column(Integer, ForeignKey("workflow.id", ondelete="cascade"))
    workflow = relationship("Workflow", foreign_keys="Run.workflow_id")
    workflow_name = association_proxy(
        "workflow", "scoped_name", info={"name": "workflow_name"}
    )
    task_id = db.Column(Integer, ForeignKey("task.id", ondelete="SET NULL"))
    task = relationship("Task", foreign_keys="Run.task_id")
    state = db.Column(db.Dict, info={"log_change": False})
    results = relationship("Result", back_populates="run", cascade="all, delete-orphan")
    model_properties = ["progress", "service_properties"]

    def __init__(self, **kwargs):
        self.runtime = kwargs.get("runtime") or app.get_time()
        super().__init__(**kwargs)
        if not self.creator:
            self.creator = self.parent.creator
        if not kwargs.get("parent_runtime"):
            self.parent_runtime = self.runtime
            self.path = str(self.service.id)
        elif self.parent_device:
            self.path = self.parent.path
        else:
            self.path = f"{self.parent.path}>{self.service.id}"
        if not self.start_services:
            self.start_services = [db.fetch("service", scoped_name="Start").id]

    @classmethod
    def prefilter(cls, query):
        return query.filter(cls.parent_runtime == cls.runtime)

    @classmethod
    def rbac_filter(cls, query, mode, user):
        query = query.join(cls.service).filter(
            models["service"].default_access != "admin"
        )
        public_services = query.join(cls.service).filter(
            models["service"].default_access == "public"
        )
        pool_alias = aliased(models["pool"])
        return public_services.union(
            query.join(cls.service)
            .join(models["pool"], models["service"].pools)
            .join(models["access"], models["pool"].access)
            .join(pool_alias, models["access"].user_pools)
            .join(models["user"], pool_alias.users)
            .filter(models["access"].access_type.contains(mode))
            .filter(models["user"].name == user.name),
            query.filter(cls.creator == user.name),
        )

    @property
    def name(self):
        return repr(self)

    @property
    def original(self):
        return self if not self.parent else self.parent.original

    @property
    def log_change(self):
        return self.runtime == self.parent_runtime

    def __repr__(self):
        return f"{self.runtime}: SERVICE '{self.service}'"

    def __getattr__(self, key):
        if key in self.__dict__:
            return self.__dict__[key]
        elif key in self.__dict__.get("properties", {}):
            return self.__dict__["properties"][key]
        elif set(self.__dict__) & {"service_id", "service"}:
            return getattr(self.service, key)
        else:
            raise AttributeError

    def result(self, device=None, main=False):
        for result in self.results:
            if result.device_name == device:
                return result
        if main and len(self.results) == 1:
            return self.results[0]

    @property
    def service_properties(self):
        return {k: getattr(self.service, k) for k in ("id", "type", "name")}

    @property
    def stop(self):
        if app.redis_queue:
            return bool(app.redis("get", f"stop/{self.parent_runtime}"))
        else:
            return app.run_stop[self.parent_runtime]

    def get_state(self):
        if self.state:
            return self.state
        elif app.redis_queue:
            keys = app.redis("keys", f"{self.parent_runtime}/state/*")
            if not keys:
                return {}
            data, state = list(zip(keys, app.redis("mget", *keys))), {}
            for log, value in data:
                inner_store, (*path, last_key) = state, log.split("/")[2:]
                for key in path:
                    inner_store = inner_store.setdefault(key, {})
                if value in ("False", "True"):
                    value = value == "True"
                inner_store[last_key] = value
            return state
        else:
            return app.run_db[self.parent_runtime]

    @property
    def progress(self):
        if not self.service_run:
            return
        progress = self.get_state().get(self.path, {}).get("progress")
        try:
            progress = progress["device"]
            failure = int(progress.get("failure", 0))
            success = int(progress.get("success", 0))
            return f"{success + failure}/{progress['total']} ({failure} failed)"
        except (KeyError, TypeError):
            return "N/A"

    def run(self, payload):
        self.service_run = ServiceRun(
            self,
            payload=payload,
            service=self.service,
            main_run=True,
            restart_run=self.restart_run,
            runtime=self.runtime,
            start_services=self.start_services,
        )
        return self.service_run.results

    def update_netmiko_connection(self, connection):
        for property in ("fast_cli", "timeout", "global_delay_factor"):
            service_value = getattr(self.service, property)
            if service_value:
                setattr(connection, property, service_value)
        try:
            if not hasattr(connection, "check_enable_mode"):
                self.log("error", "Netmiko 'check_enable_mode' method is missing")
                return connection
            mode = connection.check_enable_mode()
            if mode and not self.enable_mode:
                connection.exit_enable_mode()
            elif self.enable_mode and not mode:
                connection.enable()
        except Exception as exc:
            self.log("error", f"Failed to honor the enable mode {exc}")
        try:
            if not hasattr(connection, "check_config_mode"):
                self.log("error", "Netmiko 'check_config_mode' method is missing")
                return connection
            mode = connection.check_config_mode()
            if mode and not self.config_mode:
                connection.exit_config_mode()
            elif self.config_mode and not mode:
                connection.config_mode()
        except Exception as exc:
            self.log("error", f"Failed to honor the config mode {exc}")
        return connection

    def netmiko_connection(self, device):
        connection = self.get_or_close_connection("netmiko", device.name)
        if connection:
            self.log("info", "Using cached Netmiko connection", device)
            return self.update_netmiko_connection(connection)
        self.log(
            "info",
            "OPENING Netmiko connection",
            device,
            change_log=False,
            logger="security",
        )
        driver = device.netmiko_driver if self.use_device_driver else self.driver
        netmiko_connection = ConnectHandler(
            device_type=driver,
            ip=device.ip_address,
            port=device.port,
            fast_cli=self.fast_cli,
            timeout=self.timeout,
            global_delay_factor=self.global_delay_factor,
            session_log=BytesIO(),
            global_cmd_verify=False,
            **self.get_credentials(device),
        )
        if self.enable_mode:
            netmiko_connection.enable()
        if self.config_mode:
            netmiko_connection.config_mode()
        app.connections_cache["netmiko"][self.parent_runtime][
            device.name
        ] = netmiko_connection
        return netmiko_connection

    def scrapli_connection(self, device):
        connection = self.get_or_close_connection("scrapli", device.name)
        if connection:
            self.log("info", "Using cached Scrapli connection", device)
            return connection
        self.log(
            "info",
            "OPENING Scrapli connection",
            device,
            change_log=False,
            logger="security",
        )
        credentials = self.get_credentials(device)
        connection = Scrapli(
            transport=self.transport,
            platform=device.scrapli_driver if self.use_device_driver else self.driver,
            host=device.ip_address,
            auth_username=credentials["username"],
            auth_password=credentials["password"],
            auth_private_key=False,
            auth_strict_key=False,
        )
        connection.open()
        app.connections_cache["scrapli"][self.parent_runtime][device.name] = connection
        return connection

    def napalm_connection(self, device):
        connection = self.get_or_close_connection("napalm", device.name)
        if connection:
            self.log("info", "Using cached NAPALM connection", device)
            return connection
        self.log(
            "info",
            "OPENING Napalm connection",
            device,
            change_log=False,
            logger="security",
        )
        credentials = self.get_credentials(device)
        optional_args = self.service.optional_args
        if not optional_args:
            optional_args = {}
        if "secret" not in optional_args:
            optional_args["secret"] = credentials.pop("secret")
        driver = get_network_driver(
            device.napalm_driver if self.use_device_driver else self.driver
        )
        napalm_connection = driver(
            hostname=device.ip_address,
            timeout=self.timeout,
            optional_args=optional_args,
            **credentials,
        )
        napalm_connection.open()
        app.connections_cache["napalm"][self.parent_runtime][
            device.name
        ] = napalm_connection
        return napalm_connection

    def get_or_close_connection(self, library, device):
        connection = self.get_connection(library, device)
        if not connection:
            return
        if self.start_new_connection:
            return self.disconnect(library, device, connection)
        if library == "napalm":
            if connection.is_alive():
                return connection
            else:
                self.disconnect(library, device, connection)
        else:
            try:
                if library == "netmiko":
                    connection.find_prompt()
                else:
                    connection.get_prompt()
                return connection
            except Exception:
                self.disconnect(library, device, connection)

    def get_connection(self, library, device):
        cache = app.connections_cache[library].get(self.parent_runtime, {})
        return cache.get(device)

    def close_device_connection(self, device):
        for library in ("netmiko", "napalm", "scrapli"):
            connection = self.get_connection(library, device)
            if connection:
                self.disconnect(library, device, connection)

    def close_remaining_connections(self):
        threads = []
        for library in ("netmiko", "napalm", "scrapli"):
            devices = list(app.connections_cache[library][self.runtime])
            for device in devices:
                connection = app.connections_cache[library][self.runtime][device]
                thread = Thread(
                    target=self.disconnect, args=(library, device, connection)
                )
                thread.start()
                threads.append(thread)
        for thread in threads:
            thread.join()

    def disconnect(self, library, device, connection):
        try:
            connection.disconnect() if library == "netmiko" else connection.close()
            app.connections_cache[library][self.parent_runtime].pop(device)
            self.log("info", f"Closed {library} connection", device)
        except Exception as exc:
            self.log(
                "error", f"Error while closing {library} connection ({exc})", device
            )

    def enter_remote_device(self, connection, device):
        if not getattr(self, "jump_on_connect", False):
            return
        connection.find_prompt()
        prompt = connection.base_prompt
        commands = list(
            filter(
                None,
                [
                    self.sub(self.jump_command, locals()),
                    self.sub(self.expect_username_prompt, locals()),
                    self.sub(self.jump_username, locals()),
                    self.sub(self.expect_password_prompt, locals()),
                    self.sub(app.get_password(self.jump_password), locals()),
                    self.sub(self.expect_prompt, locals()),
                ],
            )
        )
        for (send, expect) in zip(commands[::2], commands[1::2]):
            if not send or not expect:
                continue
            self.log(
                "info",
                f"Sent '{send if send != commands[4] else 'jump on connect password'}'"
                f", waiting for '{expect}'",
            )
            connection.send_command(
                send,
                expect_string=expect,
                auto_find_prompt=False,
                strip_prompt=False,
                strip_command=True,
                max_loops=150,
            )
        return prompt

    def exit_remote_device(self, connection, prompt, device):
        if not getattr(self, "jump_on_connect", False):
            return
        exit_command = self.sub(self.exit_command, locals())
        self.log("info", f"Exit jump server with '{exit_command}'", device)
        connection.send_command(
            exit_command,
            expect_string=prompt or None,
            auto_find_prompt=True,
            strip_prompt=False,
            strip_command=True,
        )

    def update_configuration_properties(self, path, property, device):
        try:
            with open(path / "timestamps.json", "r") as file:
                data = load(file)
        except FileNotFoundError:
            data = {}
        data[property] = {
            timestamp: getattr(device, f"last_{property}_{timestamp}")
            for timestamp in app.configuration_timestamps
        }
        with open(path / "timestamps.json", "w") as file:
            dump(data, file, indent=4)
