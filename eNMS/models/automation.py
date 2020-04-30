from builtins import __dict__ as builtins
from collections import defaultdict
from copy import deepcopy
from datetime import datetime
from functools import partial
from importlib import __import__ as importlib_import
from io import BytesIO
from json import dumps, loads
from json.decoder import JSONDecodeError
from logging import getLogger
from multiprocessing.pool import ThreadPool
from napalm import get_network_driver
from netmiko import ConnectHandler
from os import environ
from paramiko import SFTPClient
from ruamel import yaml
from re import compile, search
from requests import post
from scp import SCPClient
from sqlalchemy import Boolean, ForeignKey, Integer, or_
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import relationship
from threading import Thread
from time import sleep
from traceback import format_exc
from warnings import warn
from xmltodict import parse
from xml.parsers.expat import ExpatError

try:
    from slackclient import SlackClient
except ImportError as exc:
    warn(f"Couldn't import slackclient module ({exc})")

from eNMS import app
from eNMS.database import db
from eNMS.models.base import AbstractBase
from eNMS.models import models
from eNMS.models.inventory import Device  # noqa: F401
from eNMS.models.scheduling import Task  # noqa: F401
from eNMS.models.administration import User  # noqa: F401


@db.set_custom_properties
class Service(AbstractBase):

    __tablename__ = "service"
    type = db.Column(db.SmallString)
    __mapper_args__ = {"polymorphic_identity": "service", "polymorphic_on": type}
    id = db.Column(Integer, primary_key=True)
    name = db.Column(db.SmallString, unique=True)
    shared = db.Column(Boolean, default=False)
    scoped_name = db.Column(db.SmallString)
    last_modified = db.Column(db.SmallString, info={"dont_track_changes": True})
    description = db.Column(db.SmallString)
    number_of_retries = db.Column(Integer, default=0)
    time_between_retries = db.Column(Integer, default=10)
    max_number_of_retries = db.Column(Integer, default=100)
    positions = db.Column(db.Dict, info={"dont_track_changes": True})
    tasks = relationship("Task", back_populates="service", cascade="all,delete")
    events = relationship("Event", back_populates="service", cascade="all,delete")
    vendor = db.Column(db.SmallString)
    operating_system = db.Column(db.SmallString)
    waiting_time = db.Column(Integer, default=0)
    creator = db.Column(db.SmallString, default="")
    workflows = relationship(
        "Workflow", secondary=db.service_workflow_table, back_populates="services"
    )
    device_query = db.Column(db.LargeString)
    device_query_property = db.Column(db.SmallString, default="ip_address")
    devices = relationship(
        "Device", secondary=db.service_device_table, back_populates="services"
    )
    pools = relationship(
        "Pool", secondary=db.service_pool_table, back_populates="services"
    )
    update_pools = db.Column(Boolean, default=False)
    send_notification = db.Column(Boolean, default=False)
    send_notification_method = db.Column(db.SmallString, default="mail")
    notification_header = db.Column(db.LargeString, default="")
    display_only_failed_nodes = db.Column(Boolean, default=True)
    include_device_results = db.Column(Boolean, default=True)
    include_link_in_summary = db.Column(Boolean, default=True)
    mail_recipient = db.Column(db.SmallString)
    reply_to = db.Column(db.SmallString)
    initial_payload = db.Column(db.Dict)
    skip = db.Column(Boolean, default=False)
    skip_query = db.Column(db.LargeString)
    skip_value = db.Column(db.SmallString, default="True")
    iteration_values = db.Column(db.LargeString)
    iteration_variable_name = db.Column(db.SmallString, default="iteration_value")
    iteration_devices = db.Column(db.LargeString)
    iteration_devices_property = db.Column(db.SmallString, default="ip_address")
    preprocessing = db.Column(db.LargeString)
    postprocessing = db.Column(db.LargeString)
    postprocessing_mode = db.Column(db.SmallString, default="always")
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
    conversion_method = db.Column(db.SmallString, default="none")
    validation_method = db.Column(db.SmallString, default="none")
    content_match = db.Column(db.LargeString, default="")
    content_match_regex = db.Column(Boolean, default=False)
    dict_match = db.Column(db.Dict)
    negative_logic = db.Column(Boolean, default=False)
    delete_spaces_before_matching = db.Column(Boolean, default=False)
    run_method = db.Column(db.SmallString, default="per_device")
    status = db.Column(db.SmallString, default="Idle")

    def __init__(self, **kwargs):
        kwargs.pop("status", None)
        super().__init__(**kwargs)
        if "name" not in kwargs:
            self.set_name()

    def update(self, **kwargs):
        if kwargs["scoped_name"] != self.scoped_name:
            self.set_name(kwargs["scoped_name"])
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
                    name=name, scoped_name=scoped_name, shared=False
                )
                break
        if workflow:
            workflow.services.append(service)
        return service

    @property
    def filename(self):
        return app.strip_all(self.name)

    def set_name(self, name=None):
        if self.shared:
            workflow = "[Shared] "
        elif not self.workflows:
            workflow = ""
        else:
            workflow = f"[{self.workflows[0].name}] "
        self.name = f"{workflow}{name or self.scoped_name}"

    def adjacent_services(self, workflow, direction, subtype):
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
    dont_track_changes = True
    id = db.Column(Integer, primary_key=True)
    success = db.Column(Boolean, default=False)
    runtime = db.Column(db.SmallString)
    duration = db.Column(db.SmallString)
    result = db.Column(db.Dict)
    run_id = db.Column(Integer, ForeignKey("run.id", ondelete="cascade"))
    run = relationship("Run", back_populates="results", foreign_keys="Result.run_id")
    parent_runtime = db.Column(db.SmallString)
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

    @classmethod
    def filtering_constraints(cls, **kwargs):
        constraints = []
        if not kwargs.get("full_result"):
            constraints.append(
                getattr(
                    models["result"],
                    "device" if kwargs["instance"]["type"] == "device" else "service",
                ).has(id=kwargs["instance"]["id"])
            )
        if kwargs.get("runtime"):
            constraints.append(models["result"].parent_runtime == kwargs["runtime"])
        return constraints


class ServiceLog(AbstractBase):

    __tablename__ = type = "service_log"
    private = True
    dont_track_changes = True
    id = db.Column(Integer, primary_key=True)
    content = db.Column(db.LargeString)
    runtime = db.Column(db.SmallString)
    service_id = db.Column(Integer, ForeignKey("service.id"))
    service = relationship("Service", foreign_keys="ServiceLog.service_id")


class Run(AbstractBase):

    __tablename__ = type = "run"
    private = True
    id = db.Column(Integer, primary_key=True)
    restart_path = db.Column(db.SmallString)
    restart_run_id = db.Column(Integer, ForeignKey("run.id"))
    restart_run = relationship("Run", uselist=False, foreign_keys=restart_run_id)
    start_services = db.Column(db.List)
    creator = db.Column(db.SmallString, default="")
    properties = db.Column(db.Dict)
    success = db.Column(Boolean, default=False)
    status = db.Column(db.SmallString, default="Running")
    runtime = db.Column(db.SmallString)
    duration = db.Column(db.SmallString)
    trigger = db.Column(db.SmallString, default="UI")
    parent_id = db.Column(Integer, ForeignKey("run.id", ondelete="cascade"))
    parent = relationship(
        "Run", remote_side=[id], foreign_keys="Run.parent_id", back_populates="children"
    )
    children = relationship("Run", foreign_keys="Run.parent_id")
    parent_runtime = db.Column(db.SmallString)
    path = db.Column(db.SmallString)
    parent_device_id = db.Column(Integer, ForeignKey("device.id"))
    parent_device = relationship("Device", foreign_keys="Run.parent_device_id")
    devices = relationship(
        "Device", secondary=db.run_device_table, back_populates="runs"
    )
    pools = relationship("Pool", secondary=db.run_pool_table, back_populates="runs")
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
    state = db.Column(db.Dict, info={"dont_track_changes": True})
    results = relationship("Result", back_populates="run", cascade="all, delete-orphan")
    model_properties = ["progress", "service_properties"]

    def __init__(self, **kwargs):
        self.runtime = kwargs.get("runtime") or app.get_time()
        super().__init__(**kwargs)
        if not self.creator:
            self.creator = self.parent.creator
        if not kwargs.get("parent_runtime"):
            self.parent_runtime = self.runtime
            self.restart_path = kwargs.get("restart_path")
            self.path = str(self.service.id)
        else:
            self.path = f"{self.parent.path}>{self.service.id}"
        restart_path = self.original.restart_path
        if restart_path:
            path_ids = restart_path.split(">")
            if str(self.service.id) in path_ids:
                workflow_index = path_ids.index(str(self.service.id))
                if workflow_index == len(path_ids) - 2:
                    self.start_services = path_ids[-1].split("-")
                elif workflow_index < len(path_ids) - 2:
                    self.start_services = [path_ids[workflow_index + 1]]
        if not self.start_services:
            self.start_services = [db.fetch("service", scoped_name="Start").id]

    @classmethod
    def filtering_constraints(cls, **_):
        return [cls.parent_runtime == cls.runtime]

    @property
    def name(self):
        return repr(self)

    @property
    def original(self):
        return self if not self.parent else self.parent.original

    @property
    def dont_track_changes(self):
        return self.runtime != self.parent_runtime

    def __repr__(self):
        return f"{self.runtime}: SERVICE '{self.service}'"

    def __getattr__(self, key):
        if key in self.__dict__:
            return self.__dict__[key]
        elif key in self.__dict__.get("properties", {}):
            return self.__dict__["properties"][key]
        elif self.__dict__.get("service_id"):
            return getattr(self.service, key)
        else:
            raise AttributeError

    def result(self, device=None):
        result = [r for r in self.results if r.device_name == device]
        return result.pop() if result else None

    @property
    def service_properties(self):
        return {k: getattr(self.service, k) for k in ("id", "type", "name")}

    @property
    def run_state(self):
        if self.state:
            return self.state
        elif self.runtime == self.parent_runtime:
            return app.run_db[self.runtime]
        else:
            return app.run_db[self.parent_runtime]["services"][self.path]

    @property
    def edge_state(self):
        return app.run_db[self.parent_runtime]["edges"]

    @property
    def stop(self):
        return app.run_stop[self.parent_runtime]

    @property
    def progress(self):
        if self.status == "Running" and self.run_state.get("progress"):
            progress = self.run_state["progress"]["device"]
            try:
                return (
                    f"{progress['success'] + progress['failure']}/{progress['total']}"
                    f" ({progress['failure']} failed)"
                )
            except KeyError:
                return "N/A"
        else:
            return "N/A"

    def compute_devices_from_query(_self, query, property, **locals):  # noqa: N805
        values = _self.eval(query, **locals)[0]
        devices, not_found = set(), []
        if isinstance(values, str):
            values = [values]
        for value in values:
            device = db.fetch("device", allow_none=True, **{property: value})
            if device:
                devices.add(device)
            else:
                not_found.append(value)
        if not_found:
            raise Exception(f"Device query invalid targets: {', '.join(not_found)}")
        return devices

    def compute_devices(self, payload):
        service = self.placeholder or self.service
        devices = set(self.devices)
        for pool in self.pools:
            devices |= set(pool.devices)
        if not devices:
            if service.device_query:
                devices |= self.compute_devices_from_query(
                    service.device_query,
                    service.device_query_property,
                    payload=payload,
                )
            devices |= set(service.devices)
            for pool in service.pools:
                if self.update_pools:
                    pool.compute_pool()
                devices |= set(pool.devices)
        return list(devices)

    def init_state(self):
        state = {
            "status": "Idle",
            "success": None,
            "progress": {
                "device": {"total": 0, "success": 0, "failure": 0, "skipped": 0}
            },
            "attempt": 0,
            "waiting_time": {
                "total": self.service.waiting_time,
                "left": self.service.waiting_time,
            },
            "summary": {"success": [], "failure": []},
        }
        if self.placeholder:
            state["placeholder"] = self.placeholder.get_properties()
        if self.service.type == "workflow":
            state.update({"edges": defaultdict(int), "services": defaultdict(dict)})
            state["progress"]["service"] = {
                "total": len(self.service.services),
                "success": 0,
                "failure": 0,
                "skipped": 0,
            }
        if self.runtime == self.parent_runtime:
            if self.runtime in app.run_db:
                return
            app.run_db[self.runtime] = state
        else:
            service_states = app.run_db[self.parent_runtime]["services"]
            if self.path not in service_states:
                service_states[self.path] = state

    def run(self, payload):
        self.init_state()
        self.run_state["status"] = "Running"
        start = datetime.now().replace(microsecond=0)
        try:
            app.service_db[self.service.id]["runs"] += 1
            self.service.status = "Running"
            db.session.commit()
            results = {"runtime": self.runtime, **self.device_run(payload)}
        except Exception:
            result = (
                f"Running {self.service.type} '{self.service.name}'"
                " raised the following exception:\n"
                f"{chr(10).join(format_exc().splitlines())}\n\n"
                "Run aborted..."
            )
            self.log("error", result)
            results = {"success": False, "runtime": self.runtime, "result": result}
        finally:
            db.session.commit()
            results["summary"] = self.run_state.get("summary", None)
            self.status = "Aborted (STOP)" if self.stop else "Completed"
            self.run_state["status"] = self.status
            if self.run_state["success"] is not False:
                self.success = self.run_state["success"] = results["success"]
            if self.send_notification:
                results = self.notify(results)
            app.service_db[self.service.id]["runs"] -= 1
            if not app.service_db[self.id]["runs"]:
                self.service.status = "Idle"
            results["duration"] = self.duration = str(
                datetime.now().replace(microsecond=0) - start
            )
            if self.runtime == self.parent_runtime:
                self.state = results["state"] = app.run_db.pop(self.runtime)
                self.close_remaining_connections()
            if self.task and not (self.task.frequency or self.task.crontab_expression):
                self.task.is_active = False
            results["properties"] = {
                "run": {
                    k: v
                    for k, v in self.properties.items()
                    if k not in db.private_properties
                },
                "service": self.service.get_properties(exclude=["positions"]),
            }
            results["trigger"] = self.trigger
            if (
                self.runtime == self.parent_runtime
                or len(self.devices) > 1
                or self.run_method == "once"
            ):
                results = self.create_result(results)
            db.session.commit()
        return results

    def make_results_json_compliant(self, results):
        def rec(value):
            if isinstance(value, dict):
                return {k: rec(v) for k, v in value.items()}
            elif isinstance(value, list):
                return list(map(rec, value))
            elif not isinstance(value, (int, str, bool, float, None.__class__)):
                self.log("info", f"Converting {value} to string in results")
                return str(value)
            else:
                return value

        return rec(results)

    @staticmethod
    def get_device_result(args):
        device_id, runtime, payload, results = args
        device = db.fetch("device", id=device_id)
        run = db.fetch("run", runtime=runtime)
        results.append(run.get_results(payload, device))

    def device_iteration(self, payload, device):
        derived_devices = self.compute_devices_from_query(
            self.service.iteration_devices,
            self.service.iteration_devices_property,
            **locals(),
        )
        derived_run = db.factory(
            "run",
            **{
                "service": self.service.id,
                "devices": [derived_device.id for derived_device in derived_devices],
                "workflow": self.workflow.id,
                "parent_device": device.id,
                "restart_run": self.restart_run,
                "parent": self,
                "parent_runtime": self.parent_runtime,
            },
        )
        derived_run.properties = self.properties
        success = derived_run.run(payload)["success"]
        key = "success" if success else "failure"
        self.run_state["summary"][key].append(device.name)
        return success

    def device_run(self, payload):
        self.devices = self.compute_devices(payload)
        if self.run_method != "once":
            self.run_state["progress"]["device"]["total"] += len(self.devices)
        if self.iteration_devices and not self.parent_device:
            if not self.workflow:
                return {
                    "success": False,
                    "result": "Device iteration not allowed outside of a workflow",
                    "runtime": self.runtime,
                }
            results = [
                self.device_iteration(payload, device) for device in self.devices
            ]
            return {"success": all(results), "runtime": self.runtime}
        elif self.run_method != "per_device":
            return self.get_results(payload)
        else:
            if self.parent_runtime == self.runtime and not self.devices:
                error = (
                    "The service 'Run method' is set to 'Per device' mode, "
                    "but no targets have been selected (in Step 3 > Targets)."
                )
                self.log("error", error)
                return {
                    "success": False,
                    "runtime": self.runtime,
                    "result": error,
                }
            if self.multiprocessing and len(self.devices) > 1:
                results = []
                processes = min(len(self.devices), self.max_processes)
                process_args = [
                    (device.id, self.runtime, payload, results)
                    for device in self.devices
                ]
                pool = ThreadPool(processes=processes)
                pool.map(self.get_device_result, process_args)
                pool.close()
                pool.join()
            else:
                results = [
                    self.get_results(payload, device, commit=False)
                    for device in self.devices
                ]
            return {
                "success": all(result["success"] for result in results),
                "runtime": self.runtime,
            }

    def create_result(self, results, device=None):
        self.success = results["success"]
        results = self.make_results_json_compliant(results)
        result_kw = {
            "run": self,
            "service": self.service_id,
            "parent_runtime": self.parent_runtime,
        }
        if self.workflow_id:
            result_kw["workflow"] = self.workflow_id
        if self.parent_device_id:
            result_kw["parent_device"] = self.parent_device_id
        if device:
            result_kw["device"] = device.id
        if self.parent_runtime == self.runtime and not device:
            for service_id, log in app.run_logs.pop(self.runtime, {}).items():
                db.factory(
                    "service_log",
                    runtime=self.runtime,
                    service=service_id,
                    content="\n".join(log),
                )
            if self.trigger == "REST":
                results["devices"] = {}
                for result in self.results:
                    results["devices"][result.device.name] = result.result
        result = db.factory("result", result=results, **result_kw)
        return results

    def run_service_job(self, payload, device):
        args = (device,) if device else ()
        retries, total_retries = self.number_of_retries + 1, 0
        while retries and total_retries < self.max_number_of_retries:
            if self.stop:
                self.log("error", f"ABORTING {device.name} (STOP)")
                return {"success": False, "result": "Aborted (STOP)"}
            retries -= 1
            total_retries += 1
            try:
                if self.number_of_retries - retries:
                    retry = self.number_of_retries - retries
                    self.log("error", f"RETRY n°{retry}", device)
                try:
                    _, exec_variables = self.eval(
                        self.service.preprocessing, function="exec", **locals()
                    )
                except SystemExit:
                    pass
                results = self.service.job(self, payload, *args)
                if device and (
                    getattr(self, "close_connection", False)
                    or self.runtime == self.parent_runtime
                ):
                    self.close_device_connection(device.name)
                self.convert_result(results)
                if "success" not in results:
                    results["success"] = True
                if (
                    self.postprocessing_mode == "always"
                    or self.postprocessing_mode == "failure"
                    and not results["success"]
                    or self.postprocessing_mode == "success"
                    and results["success"]
                ):
                    try:
                        _, exec_variables = self.eval(
                            self.service.postprocessing, function="exec", **locals()
                        )
                        if isinstance(exec_variables.get("retries"), int):
                            retries = exec_variables["retries"]
                    except SystemExit:
                        pass
                if results["success"] and self.validation_method != "none":
                    self.validate_result(results, payload, device)
                if self.negative_logic:
                    results["success"] = not results["success"]
                if results["success"]:
                    return results
                elif retries:
                    sleep(self.time_between_retries)
            except Exception as exc:
                self.log("error", str(exc), device)
                result = chr(10).join(format_exc().splitlines())
                results = {"success": False, "result": result}
        return results

    def get_results(self, payload, device=None, commit=True):
        self.log("info", "STARTING", device)
        start = datetime.now().replace(microsecond=0)
        skip_service = False
        if self.skip_query:
            skip_service = self.eval(self.skip_query, **locals())[0]
        if skip_service or self.skip:
            if device:
                self.run_state["progress"]["device"]["skipped"] += 1
                key = "success" if self.skip_value == "True" else "failure"
                self.run_state["summary"][key].append(device.name)
            return {
                "result": "skipped",
                "success": self.skip_value == "True",
            }
        results = {}
        try:
            if self.restart_run and self.service.type == "workflow":
                old_result = self.restart_run.result(
                    device=device.name if device else None
                )
                if old_result and "payload" in old_result.result:
                    payload.update(old_result["payload"])
            if self.service.iteration_values:
                targets_results = {}
                targets = self.eval(self.service.iteration_values, **locals())[0]
                if not isinstance(targets, dict):
                    targets = dict(zip(map(str, targets), targets))
                for target_name, target_value in targets.items():
                    self.payload_helper(
                        payload,
                        self.iteration_variable_name,
                        target_value,
                        device=getattr(device, "name", None),
                    )
                    targets_results[target_name] = self.run_service_job(payload, device)
                results.update(
                    {
                        "result": targets_results,
                        "success": all(r["success"] for r in targets_results.values()),
                    }
                )
            else:
                results.update(self.run_service_job(payload, device))
        except Exception:
            results.update(
                {"success": False, "result": chr(10).join(format_exc().splitlines())}
            )
            self.log("error", chr(10).join(format_exc().splitlines()), device)
        results["duration"] = str(datetime.now().replace(microsecond=0) - start)
        if device:
            status = "success" if results["success"] else "failure"
            self.run_state["progress"]["device"][status] += 1
            self.run_state["summary"][status].append(device.name)

            self.create_result({"runtime": app.get_time(), **results}, device)
        self.log("info", "FINISHED", device)
        if self.waiting_time:
            self.log("info", f"SLEEP {self.waiting_time} seconds...", device)
            sleep(self.waiting_time)
        if commit:
            db.session.commit()
        return results

    def log(
        self,
        severity,
        log,
        device=None,
        changelog=False,
        logger=None,
        service_log=True,
    ):
        log_level = int(self.original.log_level)
        if not log_level or severity not in app.log_levels[log_level - 1 :]:
            return
        if device:
            device_name = device if isinstance(device, str) else device.name
            log = f"DEVICE {device_name} - {log}"
        log = f"USER {self.creator} - SERVICE {self.service.scoped_name} - {log}"
        settings = app.log(
            severity, log, user=self.creator, changelog=changelog, logger=logger
        )
        if service_log or logger and settings.get("service_log"):
            run_log = f"{app.get_time()} - {severity} - {log}"
            app.run_logs[self.parent_runtime][self.service_id].append(run_log)
            if self.runtime != self.parent_runtime:
                parent_id = self.original.service_id
                app.run_logs[self.parent_runtime][parent_id].append(run_log)

    def build_notification(self, results):
        notification = {
            "Service": f"{self.service.name} ({self.service.type})",
            "Runtime": self.runtime,
            "Status": "PASS" if results["success"] else "FAILED",
        }
        if "result" in results:
            notification["Results"] = results["result"]
        if self.notification_header:
            notification["Header"] = self.notification_header
        if self.include_link_in_summary:
            address = app.settings["app"]["address"]
            notification["Link"] = f"{address}/view_service_results/{self.id}"
        summary = results["summary"]
        if summary:
            if summary["failure"]:
                notification["FAILED"] = summary["failure"]
            if summary["success"] and not self.display_only_failed_nodes:
                notification["PASSED"] = summary["success"]
        return notification

    def notify(self, results):
        self.log("info", f"Sending {self.send_notification_method} notification...")
        notification = self.build_notification(results)
        file_content = deepcopy(notification)
        if self.include_device_results:
            file_content["Device Results"] = {}
            for device in self.devices:
                device_result = db.fetch(
                    "result",
                    service_id=self.service_id,
                    parent_runtime=self.parent_runtime,
                    device_id=device.id,
                    allow_none=True,
                )
                if device_result:
                    file_content["Device Results"][device.name] = device_result.result
        try:
            if self.send_notification_method == "mail":
                filename = self.runtime.replace(".", "").replace(":", "")
                status = "PASS" if results["success"] else "FAILED"
                result = app.send_email(
                    f"{status}: {self.service.name}",
                    app.str_dict(notification),
                    recipients=self.mail_recipient,
                    reply_to=self.reply_to,
                    filename=f"results-{filename}.txt",
                    file_content=app.str_dict(file_content),
                )
            elif self.send_notification_method == "slack":
                result = SlackClient(environ.get("SLACK_TOKEN")).api_call(
                    "chat.postMessage",
                    channel=app.settings["slack"]["channel"],
                    text=notification,
                )
            else:
                result = post(
                    app.settings["mattermost"]["url"],
                    verify=app.settings["mattermost"]["verify_certificate"],
                    data=dumps(
                        {
                            "channel": app.settings["mattermost"]["channel"],
                            "text": notification,
                        }
                    ),
                ).text
            results["notification"] = {"success": True, "result": result}
        except Exception:
            results["notification"] = {
                "success": False,
                "error": "\n".join(format_exc().splitlines()),
            }
        return results

    def get_credentials(self, device):
        if self.credentials == "device":
            return device.username, app.get_password(device.password)
        elif self.credentials == "user":
            user = db.fetch("user", name=self.creator)
            return user.name, app.get_password(user.password)
        else:
            return (
                self.sub(self.custom_username, locals()),
                app.get_password(self.sub(self.custom_password, locals())),
            )

    def convert_result(self, result):
        if self.conversion_method == "none" or "result" not in result:
            return result
        try:
            if self.conversion_method == "text":
                result["result"] = str(result["result"])
            elif self.conversion_method == "json":
                result["result"] = loads(result["result"])
            elif self.conversion_method == "xml":
                result["result"] = parse(result["result"])
        except (ExpatError, JSONDecodeError) as exc:
            result = {
                "success": False,
                "text_response": result,
                "error": f"Conversion to {self.conversion_method} failed",
                "exception": str(exc),
            }
        return result

    def validate_result(self, results, payload, device):
        if self.validation_method == "text":
            match = self.sub(self.content_match, locals())
            str_result = str(results["result"])
            if self.delete_spaces_before_matching:
                match, str_result = map(self.space_deleter, (match, str_result))
            success = (
                self.content_match_regex
                and bool(search(match, str_result))
                or match in str_result
                and not self.content_match_regex
            )
        else:
            match = self.sub(self.dict_match, locals())
            success = self.match_dictionary(results["result"], match)
        results.update({"match": match, "success": success})

    def match_dictionary(self, result, match, first=True):
        if self.validation_method == "dict_equal":
            return result == self.dict_match
        else:
            match_copy = deepcopy(match) if first else match
            if isinstance(result, dict):
                for k, v in result.items():
                    if k in match_copy and match_copy[k] == v:
                        match_copy.pop(k)
                    else:
                        self.match_dictionary(v, match_copy, False)
            elif isinstance(result, list):
                for item in result:
                    self.match_dictionary(item, match_copy, False)
            return not match_copy

    def transfer_file(self, ssh_client, files):
        if self.protocol == "sftp":
            with SFTPClient.from_transport(
                ssh_client.get_transport(),
                window_size=self.window_size,
                max_packet_size=self.max_transfer_size,
            ) as sftp:
                for source, destination in files:
                    getattr(sftp, self.direction)(source, destination)
        else:
            with SCPClient(ssh_client.get_transport()) as scp:
                for source, destination in files:
                    getattr(scp, self.direction)(source, destination)

    def payload_helper(
        self,
        payload,
        name,
        value=None,
        device=None,
        section=None,
        operation="set",
        allow_none=False,
    ):
        payload = payload.setdefault("variables", {})
        if device:
            payload = payload.setdefault("devices", {})
            payload = payload.setdefault(device, {})
        if section:
            payload = payload.setdefault(section, {})
        if value is not None:
            if operation == "set":
                payload[name] = value
            else:
                getattr(payload[name], operation)(value)
        else:
            if name not in payload and not allow_none:
                raise Exception(f"Payload Editor: {name} not found in {payload}.")
            return payload.get(name)

    def get_var(self, payload, name, device=None, **kwargs):
        return self.payload_helper(payload, name, device=device, **kwargs)

    def get_result(self, service_name, device=None, workflow=None):
        def filter_run(query, property):
            query = query.filter(
                models["run"].service.has(
                    getattr(models["service"], property) == service_name
                )
            )
            return query.all()

        def recursive_search(run: "Run"):
            if not run:
                return None
            query = db.session.query(models["run"]).filter(
                models["run"].parent_runtime == run.parent_runtime
            )
            if workflow or self.workflow:
                name = workflow or self.workflow.name
                query.filter(
                    models["run"].workflow.has(models["workflow"].name == name)
                )
            runs = filter_run(query, "scoped_name") or filter_run(query, "name")
            results = list(filter(None, [run.result(device) for run in runs]))
            if not results:
                return recursive_search(run.restart_run)
            else:
                return results.pop().result

        return recursive_search(self)

    @staticmethod
    def _import(module, *args, **kwargs):
        if module in app.settings["security"]["forbidden_python_libraries"]:
            raise ImportError(f"Module '{module}' is restricted.")
        return importlib_import(module, *args, **kwargs)

    def global_variables(_self, **locals):  # noqa: N805
        payload, device = locals.get("payload", {}), locals.get("device")
        variables = {
            "__builtins__": {**builtins, "__import__": _self._import},
            "send_email": app.send_email,
            "settings": app.settings,
            "devices": _self.devices,
            "get_var": partial(_self.get_var, payload),
            "get_result": _self.get_result,
            "log": _self.log,
            "workflow": _self.workflow,
            "set_var": partial(_self.payload_helper, payload),
            "parent_device": _self.parent_device or device,
            **locals,
        }
        if "variables" not in payload:
            return variables
        variables.update(
            {k: v for k, v in payload["variables"].items() if k != "devices"}
        )
        if "devices" in payload["variables"] and device:
            variables.update(payload["variables"]["devices"].get(device.name, {}))
        return variables

    def eval(_self, query, function="eval", **locals):  # noqa: N805
        exec_variables = _self.global_variables(**locals)
        results = builtins[function](query, exec_variables)
        return results, exec_variables

    def sub(self, input, variables):
        r = compile("{{(.*?)}}")

        def replace(match):
            return str(self.eval(match.group()[2:-2], **variables)[0])

        def rec(input):
            if isinstance(input, str):
                return r.sub(replace, input)
            elif isinstance(input, list):
                return [rec(x) for x in input]
            elif isinstance(input, dict):
                return {rec(k): rec(v) for k, v in input.items()}
            else:
                return input

        return rec(input)

    def space_deleter(self, input):
        return "".join(input.split())

    def update_netmiko_connection(self, connection):
        for property in ("fast_cli", "timeout", "global_delay_factor"):
            service_value = getattr(self.service, property)
            if service_value:
                setattr(connection, property, service_value)
        try:
            if not hasattr(connection, "check_config_mode"):
                self.log("error", f"Netmiko 'check_config_mode' method is missing.")
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
            "info", "OPENING Netmiko connection", device, logger="security",
        )
        username, password = self.get_credentials(device)
        driver = device.netmiko_driver if self.use_device_driver else self.driver
        netmiko_connection = ConnectHandler(
            device_type=driver,
            ip=device.ip_address,
            port=device.port,
            username=username,
            password=password,
            secret=app.get_password(device.enable_password),
            fast_cli=self.fast_cli,
            timeout=self.timeout,
            global_delay_factor=self.global_delay_factor,
            session_log=BytesIO(),
        )
        if self.enable_mode:
            netmiko_connection.enable()
        if self.config_mode:
            netmiko_connection.config_mode()
        app.connections_cache["netmiko"][self.parent_runtime][
            device.name
        ] = netmiko_connection
        return netmiko_connection

    def napalm_connection(self, device):
        connection = self.get_or_close_connection("napalm", device.name)
        if connection:
            self.log("info", "Using cached NAPALM connection", device)
            return connection
        self.log(
            "info", "OPENING Napalm connection", device, logger="security",
        )
        username, password = self.get_credentials(device)
        optional_args = self.service.optional_args
        if not optional_args:
            optional_args = {}
        if "secret" not in optional_args:
            optional_args["secret"] = device.enable_password
        driver = get_network_driver(
            device.napalm_driver if self.use_device_driver else self.driver
        )
        napalm_connection = driver(
            hostname=device.ip_address,
            username=username,
            password=password,
            timeout=self.timeout,
            optional_args=optional_args,
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
                connection.find_prompt()
                return connection
            except Exception:
                self.disconnect(library, device, connection)

    def get_connection(self, library, device):
        cache = app.connections_cache[library].get(self.parent_runtime, {})
        return cache.get(device)

    def close_device_connection(self, device):
        for library in ("netmiko", "napalm"):
            connection = self.get_connection(library, device)
            if connection:
                self.disconnect(library, device, connection)

    def close_remaining_connections(self):
        threads = []
        for library in ("netmiko", "napalm"):
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
            self.log("info", f"Sent '{send}', waiting for '{expect}'", device)
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

    def generate_yaml_file(self, path, device):
        data = {
            "last_failure": device.last_failure,
            "last_runtime": device.last_runtime,
            "last_update": device.last_update,
            "last_status": device.last_status,
        }
        with open(path / "data.yml", "w") as file:
            yaml.dump(data, file, default_flow_style=False)
