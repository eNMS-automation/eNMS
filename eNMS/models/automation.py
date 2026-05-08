from collections import defaultdict
from copy import deepcopy
from datetime import datetime
from flask_login import current_user
from functools import wraps
from itertools import batched, chain
from orjson import loads
from os import environ, getpid
from requests import get, post
from requests.exceptions import ConnectionError, MissingSchema, ReadTimeout
from sqlalchemy import Boolean, case, ForeignKey, insert, Integer
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import backref, deferred, relationship
from threading import Thread
from time import perf_counter
from traceback import format_exc
from types import SimpleNamespace

from eNMS.controller import controller
from eNMS.database import db
from eNMS.environment import env
from eNMS.models.base import AbstractBase
from eNMS.runner import Runner
from eNMS.variables import vs


class Service(AbstractBase):
    __tablename__ = class_type = export_type = "service"
    type = db.Column(db.SmallString)
    __mapper_args__ = {"polymorphic_identity": "service", "polymorphic_on": type}
    id = db.Column(Integer, primary_key=True)
    persistent_id = db.Column(db.TinyString)
    name = db.Column(db.SmallString, unique=True)
    path = db.Column(db.TinyString, info={"log_change": False})
    creator = db.Column(db.SmallString)
    soft_deleted = db.Column(Boolean, default=False)
    shared = db.Column(Boolean, default=False)
    scoped_name = db.Column(db.SmallString, index=True)
    creation_time = db.Column(db.TinyString)
    last_modified = db.Column(db.TinyString, info={"log_change": False})
    last_modified_by = db.Column(db.SmallString, info={"log_change": False})
    last_run = db.Column(db.SmallString, info={"log_change": False})
    version = db.Column(db.SmallString)
    description = db.Column(db.LargeString)
    priority = db.Column(Integer, default=10)
    high_performance = db.Column(Boolean, default=False)
    number_of_retries = db.Column(Integer, default=0)
    time_between_retries = db.Column(Integer, default=10)
    max_number_of_retries = db.Column(Integer, default=100)
    credential_type = db.Column(db.SmallString, default="any")
    disable_result_creation = db.Column(Boolean, default=False)
    restrict_to_owners = db.Column(db.List)
    tasks = relationship("Task", back_populates="service", cascade="all,delete")
    vendor = db.Column(db.SmallString)
    operating_system = db.Column(db.SmallString)
    dry_run = db.Column(Boolean, default=False)
    waiting_time = db.Column(Integer, default=0)
    workflows = relationship(
        "Workflow", secondary=db.service_workflow_table, back_populates="services"
    )
    device_query = db.Column(db.LargeString)
    device_query_property = db.Column(db.SmallString, default="ip_address")
    runs = relationship(
        "Run", secondary=db.run_service_table, back_populates="services"
    )
    target_devices = relationship(
        "Device",
        secondary=db.service_target_device_table,
        back_populates="target_services",
    )
    target_pools = relationship(
        "Pool", secondary=db.service_target_pool_table, back_populates="target_services"
    )
    update_target_pools = db.Column(Boolean, default=False)
    report = db.Column(db.LargeString)
    report_format = db.Column(db.TinyString, default="text")
    report_jinja2_template = db.Column(Boolean, default=False)
    disabled = db.Column(Boolean, default=False)
    disabled_info = db.Column(db.TinyString)
    display_report = db.Column(Boolean, default=False)
    email_report = db.Column(Boolean, default=False)
    send_notification = db.Column(Boolean, default=False)
    send_notification_method = db.Column(db.TinyString, default="mail")
    notification_header = db.Column(db.LargeString)
    display_only_failed_nodes = db.Column(Boolean, default=True)
    include_device_results = db.Column(Boolean, default=True)
    include_link_in_summary = db.Column(Boolean, default=True)
    mail_recipient = db.Column(db.SmallString)
    mail_subject = db.Column(db.SmallString)
    mail_sender = db.Column(db.SmallString)
    mail_bcc = db.Column(db.SmallString)
    reply_to = db.Column(db.SmallString)
    initial_payload = db.Column(db.Dict)
    mandatory_parametrization = db.Column(Boolean, default=False)
    parameterized_form = db.Column(db.LargeString)
    parameterized_form_template = db.Column(db.LargeString)
    skip = db.Column(db.Dict)
    skip_query = db.Column(db.LargeString)
    skip_value = db.Column(db.SmallString, default="success")
    iteration_values = db.Column(db.LargeString)
    iteration_variable_name = db.Column(db.SmallString, default="iteration_value")
    iteration_devices = db.Column(db.LargeString)
    iteration_devices_property = db.Column(db.TinyString, default="ip_address")
    preprocessing = db.Column(db.LargeString)
    postprocessing = db.Column(db.LargeString)
    postprocessing_mode = db.Column(db.TinyString, default="success")
    builder_link = db.Column(db.SmallString, info={"log_change": False})
    log_level = db.Column(Integer, default=1)
    show_user_logs = db.Column(Boolean, default=True)
    service_logs = relationship(
        "ServiceLog",
        foreign_keys="[ServiceLog.service_id]",
        back_populates="service",
        cascade="all, delete-orphan",
    )
    reports = relationship(
        "ServiceReport",
        foreign_keys="[ServiceReport.service_id]",
        back_populates="service",
        cascade="all, delete-orphan",
    )
    logs = relationship(
        "Changelog", back_populates="service", info={"log_change": False}
    )
    maximum_runs = db.Column(Integer, default=1)
    multiprocessing = db.Column(Boolean, default=False)
    max_processes = db.Column(Integer, default=5)
    status = db.Column(db.TinyString, default="Idle")
    validation_condition = db.Column(db.TinyString, default="none")
    conversion_method = db.Column(db.TinyString, default="none")
    validation_method = db.Column(db.TinyString, default="text")
    validation_section = db.Column(db.LargeString, default="results['result']")
    content_match = db.Column(db.LargeString)
    content_match_regex = db.Column(Boolean, default=False)
    dict_match = db.Column(db.Dict)
    negative_logic = db.Column(Boolean, default=False)
    delete_spaces_before_matching = db.Column(Boolean, default=False)
    run_method = db.Column(db.TinyString, default="per_device")

    def __init__(self, **kwargs):
        kwargs.pop("status", None)
        super().__init__(**kwargs)
        if not self.persistent_id:
            self.persistent_id = vs.get_persistent_id()

    @property
    def base_properties(self):
        return {
            **super().base_properties,
            "persistent_id": self.persistent_id,
            "builder_link": self.builder_link,
            "report_format": self.report_format,
            "scoped_name": self.scoped_name,
        }

    def check_restriction_to_owners(self, mode):
        if (
            not getattr(current_user, "is_admin", True)
            and not self.shared
            and any(
                mode in getattr(workflow, "restrict_to_owners")
                and current_user not in workflow.owners
                for workflow in self.get_ancestors()
            )
        ):
            raise db.rbac_error("Not Authorized (restricted to owners).")

    def delete(self):
        if self.name in ("[Shared] Start", "[Shared] End", "[Shared] Placeholder"):
            return {"log": f"It is not allowed to delete '{self.name}'."}
        self.check_restriction_to_owners("edit")

    def duplicate(self, workflow=None):
        index = 0
        while True:
            number = f" ({index})" if index else ""
            scoped_name = f"{self.scoped_name}{number}"
            name = f"[{workflow.name}] {scoped_name}" if workflow else scoped_name
            if not db.fetch("service", allow_none=True, name=name):
                service = super().duplicate(
                    name=name, scoped_name=scoped_name, shared=False
                )
                break
            index += 1
        if workflow:
            service.target_devices = self.target_devices
            service.target_pools = self.target_pools
            workflow.services.append(service)
        service.persistent_id = vs.get_persistent_id()
        service.set_name()
        return service

    @property
    def filename(self):
        return vs.strip_all(self.name)

    def get_ancestors(self):
        def rec(service):
            return {service} | set().union(*(rec(w) for w in service.workflows))

        return rec(self)

    @property
    def is_running(self):
        if env.redis_queue:
            return bool(int(env.redis("get", f"services/{self.id}/runs")))
        else:
            return bool(vs.service_run_count[self.id])

    def post_update(self):
        if len(self.workflows) == 1 and not self.shared and self.workflows[0].path:
            self.path = f"{self.workflows[0].path}>{self.id}"
        else:
            self.path = str(self.id)
        self.set_name()
        path_id = (
            self.path
            if self.type == "workflow"
            else self.workflows[0].path if len(self.workflows) == 1 else ""
        )
        self.builder_link = (
            ">".join(
                db.fetch("service", id=id, rbac=None).persistent_id
                for id in path_id.split(">")
            )
            if path_id
            else ""
        )

    def update(self, **kwargs):
        old_name, old_disabled_status = self.name, self.disabled
        if self.path:
            self.check_restriction_to_owners("edit")
        super().update(**kwargs)
        if self.disabled and not old_disabled_status:
            self.disabled_info = f"Disabled at {vs.get_time()} by {current_user}"
        elif not self.disabled:
            self.disabled_info = ""
        if not kwargs.get("migration_import"):
            self.set_name()
            self.update_last_modified_properties()
            for workflow in self.workflows:
                workflow.positions[self.name] = workflow.positions.pop(old_name, [0, 0])

    def update_count(self, count):
        if env.redis_queue:
            env.redis("incr", f"services/{self.id}/runs", count)
        else:
            vs.service_run_count[self.id] += count

    def update_last_modified_properties(self):
        super().update_last_modified_properties()
        for ancestor in self.get_ancestors():
            ancestor.last_modified = self.last_modified
            ancestor.last_modified_by = self.last_modified_by

    def set_name(self, name=None):
        if self.shared:
            workflow = "[Shared] "
        elif not self.workflows:
            workflow = ""
        else:
            workflow = f"[{self.workflows[0].name}] "
        self.name = f"{workflow}{name or self.scoped_name}"


class ConnectionService(Service):
    __tablename__ = "connection_service"
    id = db.Column(Integer, ForeignKey("service.id"), primary_key=True)
    parent_type = "service"
    credentials = db.Column(db.SmallString, default="device")
    named_credential_id = db.Column(
        Integer, ForeignKey("credential.id", ondelete="SET NULL")
    )
    named_credential = relationship("Credential")
    custom_username = db.Column(db.SmallString)
    custom_password = db.Column(db.SmallString)
    start_new_connection = db.Column(Boolean, default=False)
    connection_name = db.Column(db.SmallString, default="default")
    close_connection = db.Column(Boolean, default=False)
    __mapper_args__ = {"polymorphic_identity": "connection_service"}


class Result(AbstractBase):
    __tablename__ = type = class_type = "result"
    private = True
    log_change = False
    id = db.Column(Integer, primary_key=True)
    name = db.Column(db.SmallString, unique=True)
    path = db.Column(db.SmallString)
    success = db.Column(Boolean, default=False)
    labels = db.Column(db.LargeString)
    runtime = db.Column(db.TinyString)
    duration = db.Column(db.TinyString)
    result = deferred(db.Column(db.Dict))
    creator = db.Column(db.SmallString)
    memory_size = db.Column(db.SmallString)
    run_id = db.Column(Integer, ForeignKey("run.id", ondelete="cascade"))
    run = relationship("Run", back_populates="results", foreign_keys="Result.run_id")
    parent_runtime = db.Column(db.TinyString, index=True)
    parent_service_id = db.Column(Integer, ForeignKey("service.id", ondelete="cascade"))
    parent_service = relationship("Service", foreign_keys="Result.parent_service_id")
    parent_service_name = association_proxy(
        "service", "scoped_name", info={"name": "parent_service_name"}
    )
    parent_device_id = db.Column(Integer, ForeignKey("device.id", ondelete="cascade"))
    parent_device = relationship("Device", uselist=False, foreign_keys=parent_device_id)
    parent_device_name = association_proxy("parent_device", "name")
    device_id = db.Column(Integer, ForeignKey("device.id", ondelete="cascade"))
    device = relationship(
        "Device",
        uselist=False,
        foreign_keys=device_id,
        backref=backref("results", cascade="all,delete"),
    )
    device_name = association_proxy("device", "name")
    service_id = db.Column(
        Integer, ForeignKey("service.id", ondelete="cascade"), index=True
    )
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
        for key in ("duration", "runtime", "success"):
            setattr(self, key, kwargs["result"][key])
        self.path = kwargs["path"]
        self.name = f"{self.runtime} - {vs.get_persistent_id()}"
        super().__init__(**kwargs)

    def __repr__(self):
        return f"SERVICE '{self.service}' - DEVICE '{self.device} ({self.runtime})"

    @classmethod
    def filtering_constraints(cls, **kwargs):
        constraints = []
        if kwargs.get("rest_api_request", False):
            return []
        if kwargs.get("runtime"):
            constraints.append(vs.models["result"].parent_runtime == kwargs["runtime"])
        return constraints


class ServiceLog(AbstractBase):
    __tablename__ = type = class_type = "service_log"
    private = True
    log_change = False
    id = db.Column(Integer, primary_key=True)
    content = db.Column(db.LargeString)
    runtime = db.Column(db.TinyString)
    service_id = db.Column(Integer, ForeignKey("service.id"))
    service = relationship("Service", foreign_keys="ServiceLog.service_id")
    service_name = association_proxy("service", "name")

    def __repr__(self):
        return f"SERVICE '{self.service}' ({self.runtime})"


class ServiceReport(AbstractBase):
    __tablename__ = type = class_type = "service_report"
    private = True
    log_change = False
    id = db.Column(Integer, primary_key=True)
    content = db.Column(db.LargeString)
    runtime = db.Column(db.TinyString, ForeignKey("run.runtime", ondelete="cascade"))
    service_id = db.Column(Integer, ForeignKey("service.id", ondelete="cascade"))
    service = relationship("Service", foreign_keys="ServiceReport.service_id")
    service_name = association_proxy("service", "name")

    def __repr__(self):
        return f"SERVICE REPORT '{self.service}' ({self.runtime})"


class Run(AbstractBase):
    __tablename__ = type = class_type = "run"
    log_change = False
    id = db.Column(Integer, primary_key=True)
    name = db.Column(db.SmallString, unique=True)
    restart_run_id = db.Column(Integer, ForeignKey("run.id", ondelete="SET NULL"))
    restart_run = relationship(
        "Run", remote_side=[id], foreign_keys="Run.restart_run_id"
    )
    start_services = db.Column(db.List)
    is_async = db.Column(Boolean, default=False)
    creator = db.Column(db.SmallString, default="")
    properties = db.Column(db.Dict)
    payload = deferred(db.Column(db.Dict))
    success = db.Column(Boolean, default=False)
    labels = db.Column(db.LargeString)
    status = db.Column(db.TinyString, default="Running")
    runtime = db.Column(db.TinyString, index=True, unique=True)
    duration = db.Column(db.TinyString)
    trigger = db.Column(db.TinyString)
    path = db.Column(db.TinyString)
    memory_size = db.Column(db.SmallString)
    parameterized_run = db.Column(Boolean, default=False)
    server_id = db.Column(Integer, ForeignKey("server.id"))
    server = relationship("Server", back_populates="runs")
    server_name = association_proxy("server", "name")
    server_version = db.Column(db.TinyString)
    server_commit_sha = db.Column(db.TinyString)
    service_id = db.Column(Integer, ForeignKey("service.id", ondelete="cascade"))
    service = relationship("Service", foreign_keys="Run.service_id")
    service_name = db.Column(db.SmallString)
    services = relationship(
        "Service", secondary=db.run_service_table, back_populates="runs"
    )
    target_devices = relationship(
        "Device", secondary=db.run_device_table, back_populates="runs"
    )
    target_pools = relationship(
        "Pool", secondary=db.run_pool_table, back_populates="runs"
    )
    placeholder_id = db.Column(Integer, ForeignKey("service.id", ondelete="SET NULL"))
    placeholder = relationship("Service", foreign_keys="Run.placeholder_id")
    task_id = db.Column(Integer, ForeignKey("task.id", ondelete="SET NULL"))
    task = relationship("Task", back_populates="runs")
    task_name = association_proxy("task", "name")
    worker_id = db.Column(Integer, ForeignKey("worker.id"))
    worker = relationship("Worker", back_populates="runs")
    worker_name = association_proxy("worker", "name")
    state = db.Column(db.Dict, info={"log_change": False})
    results = relationship("Result", back_populates="run", cascade="all, delete-orphan")
    model_properties = {
        "progress": "str",
        "server_properties": "dict",
        "service_properties": "dict",
        "worker_properties": "dict",
    }

    def __init__(self, **kwargs):
        self.runtime = kwargs.get("runtime") or vs.get_time()
        for property in ("id", "version", "commit_sha"):
            setattr(self, f"server_{property}", getattr(vs, f"server_{property}"))
        super().__init__(**kwargs)
        if not self.name:
            self.name = f"{self.runtime} ({self.creator})"
        self.path = ">".join(
            db.fetch("service", id=id, rbac=None).persistent_id
            for id in self.path.split(">")
        )
        self.service_name = (self.placeholder or self.service).name

    def __repr__(self):
        return f"{self.runtime}: SERVICE '{self.service}'"

    @staticmethod
    def _initialize():
        for run in db.fetch(
            "run",
            all_matches=True,
            allow_none=True,
            status="Running",
            server_id=vs.server_id,
            rbac=None,
        ):
            if run.worker:
                continue
            results = {"success": False, "result": "Aborted (reload)"}
            run.run_finalize(results, app_reloaded=True)
        if env.redis_queue and vs.settings["redis"]["flush_on_restart"]:
            env.redis_queue.flushdb()

    def process(commit=False, raise_exception=False):
        def decorator(func):
            def wrapper(self, *args, **kwargs):
                start_time = perf_counter()
                try:
                    if commit:
                        db.try_commit(func, self, *args, **kwargs)
                    else:
                        func(self, *args, **kwargs)
                except Exception:
                    log = f"'{func.__name__}' failed for {self.name}:\n{format_exc()}"
                    env.log("error", log)
                    if raise_exception:
                        raise
                finally:
                    elapsed = perf_counter() - start_time
                    log = f"'{func.__name__}' took {elapsed:.3f}s for {self.name}"
                    env.log("info", log, change_log=False)

            return wrapper

        return decorator

    @property
    def cache(self):
        creator = db.fetch("user", name=self.creator, rbac=None)
        return {
            "creator": {
                "name": creator.name,
                "email": creator.email,
                "is_admin": creator.is_admin,
            },
            "main_run": self.base_properties,
            "main_run_service": {
                "credential_type": self.service.credential_type,
                "high_performance": self.service.high_performance,
                "log_level": int(self.service.log_level),
                "show_user_logs": self.service.show_user_logs,
                "id": self.service.id,
            },
            "topology": self.topology,
            "global_variables": {
                "dict_to_string": vs.dict_to_string,
                "encrypt": env.encrypt_password,
                "placeholder": self.topology["services"].get(self.placeholder_id),
                "prepend_filepath": vs.prepend_filepath,
                "runtime": self.runtime,
                "send_email": env.send_email,
                "server": vs.server_dict,
                "trigger": self.trigger,
                "try_commit": db.try_commit,
                "try_set": db.try_set,
                "user": {
                    "name": creator.name,
                    "email": creator.email,
                    "is_admin": creator.is_admin,
                },
            },
        }

    @process()
    def clean_stored_data(self):
        vs.run_allowed_targets.pop(self.runtime, None)
        vs.run_states.pop(self.runtime, None)
        vs.run_logs.pop(self.runtime, None)
        vs.run_stop.pop(self.runtime, None)
        vs.run_instances.pop(self.runtime, None)
        if env.redis_queue:
            runtime_keys = env.redis("keys", f"{self.runtime}/*") or []
            if runtime_keys:
                env.redis("delete", *runtime_keys)
            env.redis("decr", f"rate_limit:{self.creator}:runs")

    @process()
    def close_remaining_connections(self):
        threads = []
        for library in ("netmiko", "napalm", "scrapli", "ncclient"):
            device_connections = vs.connections_cache[library][self.runtime]
            for device, connections in list(device_connections.items()):
                for connection in list(connections.values()):
                    args = (library, device, connection)
                    thread = Thread(target=self.runner.disconnect, args=args)
                    thread.start()
                    threads.append(thread)
        timeout = vs.automation["advanced"]["disconnect_thread_timeout"]
        for thread in threads:
            thread.join(timeout=timeout)
        for library in ("netmiko", "napalm", "scrapli", "ncclient"):
            vs.connections_cache[library].pop(self.runtime)

    @process(commit=True)
    def create_all_changelogs(self):
        changelogs = vs.service_changelog.pop(self.runtime, [])
        for batch in batched(changelogs, vs.database["transactions"]["batch_size"]):
            db.session.execute(insert(vs.models["changelog"]), batch)

    @process(commit=True)
    def create_all_logs(self):
        logs = []
        for service in self.services:
            content = "\n".join(
                env.log_queue(self.runtime, service.id, mode="get") or []
            )
            if hasattr(self, "runner"):
                content = self.runner.check_size(content, "log")
            logs.append(
                {"runtime": self.runtime, "service_id": service.id, "content": content}
            )
        db.session.execute(insert(vs.models["service_log"]), logs)

    @process(commit=True)
    def create_all_reports(self):
        reports = vs.service_report.pop(self.runtime, {})
        for batch in batched(
            (
                {"runtime": self.runtime, "service_id": service_id, "content": report}
                for service_id, report in reports.items()
            ),
            vs.database["transactions"]["batch_size"],
        ):
            db.session.execute(insert(vs.models["service_report"]), batch)

    @process(commit=True)
    def create_all_results(self):
        if env.redis_queue:
            results = (
                loads(result)
                for result in chain.from_iterable(
                    env.redis("lrange", key, 0, -1)
                    for key in env.redis("keys", f"{self.runtime}/results/*")
                )
            )
        else:
            results = (
                result
                for device_results in vs.service_result.pop(self.runtime, {}).values()
                for result_list in device_results.values()
                for result in result_list
            )
        for batch in batched(results, vs.database["transactions"]["batch_size"]):
            db.session.execute(insert(vs.models["result"]), batch)

    @process(commit=True)
    def end_of_run_transaction(self, results, app_reloaded):
        if app_reloaded:
            self.status = "Aborted (reload)"
        elif hasattr(self, "runner"):
            self.status = "Aborted" if self.runner.stop else "Completed"
            self.payload = self.runner.make_json_compliant(self.runner.payload)
        else:
            self.status = "Aborted (error)"
        self.success = results["success"]
        self.duration = results.get("duration", "Unknown")
        if app_reloaded or not self.service.is_running:
            self.service.status = "Idle"
        state = self.get_state()
        self.memory_size = state.get("memory_size", "Unknown")
        self.state = state
        if self.task and not (self.task.frequency or self.task.crontab_expression):
            self.task.is_active = False

    def get_run_targets(self):
        devices, pools = [], []
        if self.restart_run and self.payload["targets"] == "Manually defined":
            devices = db.fetch_all(
                "device", id_in=self.payload["restart_devices"], user=self.creator
            )
            pools = db.fetch_all(
                "pool", id_in=self.payload["restart_pools"], user=self.creator
            )
        elif self.restart_run and self.payload["targets"] == "Restart run":
            devices = self.restart_run.target_devices
            pools = self.restart_run.target_pools
        elif self.parameterized_run and set(self.payload["form"]) & {
            "target_devices",
            "target_pools",
            "device_query",
        }:
            device_ids = self.payload["form"].get("target_devices", [])
            pool_ids = self.payload["form"].get("target_pools", [])
            devices = set(db.fetch_all("device", id_in=device_ids, user=self.creator))
            pools = db.fetch_all("pool", id_in=pool_ids, user=self.creator)
            query = self.payload["form"].get("device_query")
            if query:
                property = self.payload["form"].get("device_query_property", "name")
                devices |= self.runner.compute_devices_from_query(query, property)
        elif self.target_devices or self.target_pools:
            devices, pools = self.target_devices, self.target_pools
        else:
            service = self.placeholder or self.service
            devices = set(getattr(service, "target_devices"))
            pools = getattr(service, "target_pools")
            query = getattr(service, "device_query")
            if query:
                property = getattr(service, "device_query_property")
                devices |= self.runner.compute_devices_from_query(query, property)
        self.target_devices, self.target_pools = list(devices), list(pools)
        db.session.commit()
        return set(devices) | set().union(*(pool.devices for pool in pools))

    def get_state(self):
        if self.state:
            return self.state
        elif env.redis_queue:
            keys = env.redis("keys", f"{self.runtime}/state/*")
            if not keys:
                return {}
            data, state = list(zip(keys, env.redis("mget", *keys))), {}
            for log, value in data:
                inner_store, (*path, last_key) = state, log.split("/")[2:]
                for key in path:
                    inner_store = inner_store.setdefault(key, {})
                if value in ("False", "True"):
                    value = value == "True"
                inner_store[last_key] = value
            return state
        else:
            return vs.run_states[self.runtime]

    @process(raise_exception=True)
    def get_topology(self):
        self.topology = {
            "devices": {},
            "pools": {},
            "services": {},
            "edges": {},
            "name_to_dict": defaultdict(dict),
            "scoped_name_to_dict": {},
            "neighbors": defaultdict(set),
        }
        instances, visited = {self.service}, set()
        while instances:
            instance = instances.pop()
            if instance in visited or instance.soft_deleted:
                continue
            if instance.name == "[Shared] Placeholder":
                instance = self.placeholder
            visited.add(instance)
            if instance.type == "workflow_edge":
                edge = SimpleNamespace(**instance.get_properties())
                self.topology["edges"][instance.id] = edge
                source_id, destination_id = instance.source_id, instance.destination_id
                if instance.source.name == "[Shared] Placeholder":
                    source_id = self.placeholder.id
                elif instance.destination.name == "[Shared] Placeholder":
                    destination_id = self.placeholder.id
                key = (instance.workflow_id, source_id)
                self.topology["neighbors"][key].add((edge.id, destination_id))
                self.topology["name_to_dict"]["edges"][instance.name] = edge
            else:
                service = SimpleNamespace(
                    **instance.get_properties(
                        exclude=["positions"], private_properties=True
                    )
                )
                service.target_devices = instance.target_devices
                service.target_pools = instance.target_pools
                self.topology["services"][instance.id] = service
                self.topology["scoped_name_to_dict"][instance.scoped_name] = service
                self.topology["name_to_dict"]["services"][instance.name] = service
            if instance.type == "workflow":
                instances |= set(instance.services) | set(instance.edges)

    def post_process_results(self, results):
        if self.trigger == "REST API" and self.service.high_performance:
            results["devices"] = {}
            for result in self.results:
                if not result.device:
                    continue
                results["devices"][result.device.name] = result.result
        return results

    @property
    def progress(self):
        progress = self.get_state().get(self.service.persistent_id, {}).get("progress")
        if not progress:
            return
        try:
            progress = progress["device"]
            failure = int(progress.get("failure", 0))
            success = int(progress.get("success", 0))
            return f"{success + failure}/{progress['total']} ({failure} failed)"
        except (KeyError, TypeError):
            return "N/A"

    def run(self):
        start_time = datetime.now()
        try:
            results = self.start_run()
        except Exception:
            log = f"Run '{self.name}' failed to run:\n{format_exc()}"
            results = {"success": False, "result": log}
            if hasattr(self, "runner"):
                self.runner.log("critical", log)
            else:
                env.log_queue(self.runtime, self.service.id, log)
        results["duration"] = str(datetime.now() - start_time)
        return self.run_finalize(results)

    def run_finalize(self, results, app_reloaded=False):
        self.run_service_table_transaction()
        if self.service.high_performance:
            self.create_all_results()
            self.create_all_reports()
            self.create_all_changelogs()
        self.create_all_logs()
        self.close_remaining_connections()
        self.end_of_run_transaction(results, app_reloaded)
        self.service.update_count(-1)
        self.clean_stored_data()
        return self.post_process_results(results)

    @process(commit=True)
    def run_service_table_transaction(self):
        if env.redis_queue:
            run_services = env.redis("smembers", f"{self.runtime}/services")
        else:
            run_services = vs.run_services.pop(self.runtime, [])
        if run_services:
            table = db.run_service_table
            values = [{"run_id": self.id, "service_id": id} for id in run_services]
            db.session.execute(table.delete().where(table.c.run_id == self.id))
            db.session.execute(table.insert(), values)

    @property
    def server_properties(self):
        return self.server.base_properties

    @property
    def service_properties(self):
        return self.service.base_properties

    def start_run(self):
        with db.session_scope():
            worker = db.factory(
                "worker",
                name=f"{vs.server} - {getpid()}",
                process_id=getpid(),
                subtype=environ.get("_", "").split("/")[-1],
                server_id=vs.server_id,
                rbac=None,
                commit=True,
            )
        self.worker = worker
        vs.run_allowed_targets[self.runtime] = set(
            device.id
            for device in controller.filtering(
                "device", properties=["id"], rbac="target", user=self.creator
            )
        )
        self.service.update_count(1)
        if not self.trigger:
            run_type = "Parameterized" if self.parameterized_run else "Regular"
            self.trigger = f"{run_type} Run"
        self.get_topology()
        kwargs = {
            "cache": self.cache,
            "payload": deepcopy(self.payload),
            "is_main_run": True,
            "parameterized_run": self.parameterized_run,
            "parent_runtime": self.runtime,
            "path": self.path,
            "properties": self.properties,
            "start_services": self.start_services,
            "topology": self.topology,
            "trigger": self.trigger,
        }
        if self.service.high_performance:
            kwargs["service"] = self.topology["services"][self.service.id]
            main_run = SimpleNamespace(**self.get_properties())
            main_run.target_devices, main_run.target_pools = None, None
            main_run.restart_run = self.restart_run
            main_run.cache = kwargs["cache"]
            main_run.service = self.topology["services"][self.service_id]
            main_run.placeholder = self.topology["services"].get(self.placeholder_id)
            self.update_target_pools()
        else:
            kwargs["service"] = self.service
            main_run = self
            kwargs["placeholder"] = self.placeholder
            kwargs["restart_run"] = self.restart_run
        self.runner = Runner(main_run, **kwargs)
        if self.service.high_performance:
            self.runner.run_targets = self.get_run_targets()
        return self.runner.start_run()

    def table_properties(self, **kwargs):
        return {"url": self.service.builder_link, **super().table_properties(**kwargs)}

    @process(raise_exception=True)
    def update_target_pools(self):
        for service in self.topology["services"].values():
            if service.update_target_pools and service.target_pools:
                for pool in service.target_pools:
                    pool.compute_pool()
        db.session.commit()

    @property
    def worker_properties(self):
        return self.worker.base_properties


class Task(AbstractBase):
    __tablename__ = type = class_type = "task"
    id = db.Column(Integer, primary_key=True)
    name = db.Column(db.SmallString, unique=True)
    description = db.Column(db.LargeString)
    creator = db.Column(db.SmallString)
    creation_time = db.Column(db.TinyString)
    last_modified = db.Column(db.TinyString, info={"log_change": False})
    last_modified_by = db.Column(db.SmallString, info={"log_change": False})
    last_scheduled_by = db.Column(db.SmallString)
    scheduling_mode = db.Column(db.TinyString, default="standard")
    frequency = db.Column(Integer)
    frequency_unit = db.Column(db.TinyString, default="seconds")
    start_date = db.Column(db.TinyString)
    end_date = db.Column(db.TinyString)
    crontab_expression = db.Column(db.TinyString)
    is_active = db.Column(Boolean, default=False)
    initial_payload = db.Column(db.Dict)
    devices = relationship(
        "Device", secondary=db.task_device_table, back_populates="tasks"
    )
    pools = relationship("Pool", secondary=db.task_pool_table, back_populates="tasks")
    runs = relationship("Run", back_populates="task")
    logs = relationship("Changelog", back_populates="task")
    service_id = db.Column(Integer, ForeignKey("service.id"))
    service = relationship("Service", back_populates="tasks")
    service_name = association_proxy("service", "name")
    model_properties = {
        "next_run_time": "str",
        "service_properties": "dict",
        "status": "str",
        "time_before_next_run": "str",
    }

    def _catch_request_exceptions(func):  # noqa: N805
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except (ConnectionError, MissingSchema, ReadTimeout):
                return "Scheduler Unreachable"
            except Exception as exc:
                return f"Error ({exc})"

        return wrapper

    def delete(self):
        post(f"{vs.scheduler_address}/delete_job/{self.id}")

    @property
    def service_properties(self):
        return self.service.base_properties

    @property
    @_catch_request_exceptions
    def next_run_time(self):
        return get(
            f"{vs.scheduler_address}/next_runtime/{self.id}", timeout=0.01
        ).json()

    @_catch_request_exceptions
    def schedule(self, mode="schedule"):
        try:
            payload = {"mode": mode, "task": self.get_properties()}
            result = post(f"{vs.scheduler_address}/schedule", json=payload).json()
            if not current_user.is_admin or not self.last_scheduled_by:
                self.last_scheduled_by = current_user.name
        except ConnectionError:
            return {"alert": "Scheduler Unreachable: the task cannot be scheduled."}
        self.is_active = result.get("active", False)
        return result

    @hybrid_property
    def status(self):
        return "Active" if self.is_active else "Inactive"

    @status.expression
    def status(cls):  # noqa: N805
        return case((cls.is_active, "Active"), else_="Inactive")

    @property
    @_catch_request_exceptions
    def time_before_next_run(self):
        return get(f"{vs.scheduler_address}/time_left/{self.id}", timeout=0.01).json()

    def post_update(self):
        self.schedule(mode="schedule" if self.is_active else "pause")
