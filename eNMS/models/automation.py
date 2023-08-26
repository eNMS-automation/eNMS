from copy import deepcopy
from flask_login import current_user
from functools import wraps
from os import environ, getpid
from requests import get, post
from requests.exceptions import ConnectionError, MissingSchema, ReadTimeout
from sqlalchemy import Boolean, case, ForeignKey, Integer
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import deferred, relationship

from eNMS.controller import controller
from eNMS.database import db
from eNMS.environment import env
from eNMS.models.base import AbstractBase
from eNMS.models.inventory import Device  # noqa: F401
from eNMS.models.administration import User  # noqa: F401
from eNMS.runner import Runner
from eNMS.variables import vs


class Service(AbstractBase):
    __tablename__ = class_type = export_type = "service"
    type = db.Column(db.SmallString)
    __mapper_args__ = {"polymorphic_identity": "service", "polymorphic_on": type}
    id = db.Column(Integer, primary_key=True)
    name = db.Column(db.SmallString, unique=True)
    path = db.Column(db.TinyString)
    creator = db.Column(db.SmallString)
    admin_only = db.Column(Boolean, default=False)
    shared = db.Column(Boolean, default=False)
    scoped_name = db.Column(db.SmallString, index=True)
    last_modified = db.Column(db.TinyString, info={"log_change": False})
    last_modified_by = db.Column(db.SmallString, info={"log_change": False})
    last_run = db.Column(db.SmallString, info={"log_change": False})
    description = db.Column(db.LargeString)
    priority = db.Column(Integer, default=10)
    number_of_retries = db.Column(Integer, default=0)
    time_between_retries = db.Column(Integer, default=10)
    max_number_of_retries = db.Column(Integer, default=100)
    credential_type = db.Column(db.SmallString, default="any")
    positions = db.Column(db.Dict, info={"log_change": False})
    disable_result_creation = db.Column(Boolean, default=False)
    restrict_to_owners = db.Column(db.List)
    tasks = relationship("Task", back_populates="service", cascade="all,delete")
    vendor = db.Column(db.SmallString)
    operating_system = db.Column(db.SmallString)
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
    update_pools_after_running = db.Column(Boolean, default=False)
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
    reply_to = db.Column(db.SmallString)
    initial_payload = db.Column(db.Dict)
    mandatory_parametrization = db.Column(Boolean, default=False)
    parameterized_form = db.Column(db.LargeString)
    parameterized_form_template = db.Column(db.LargeString)
    skip = db.Column(db.Dict)
    skip_query = db.Column(db.LargeString)
    skip_value = db.Column(db.SmallString, default="True")
    iteration_values = db.Column(db.LargeString)
    iteration_variable_name = db.Column(db.SmallString, default="iteration_value")
    iteration_devices = db.Column(db.LargeString)
    iteration_devices_property = db.Column(db.TinyString, default="ip_address")
    preprocessing = db.Column(db.LargeString)
    postprocessing = db.Column(db.LargeString)
    postprocessing_mode = db.Column(db.TinyString, default="success")
    log_level = db.Column(Integer, default=1)
    logs = relationship(
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

    @property
    def base_properties(self):
        return {**super().base_properties, "report_format": self.report_format}

    def delete(self):
        if self.name in ("[Shared] Start", "[Shared] End", "[Shared] Placeholder"):
            return {"log": f"It is not allowed to delete '{self.name}'."}
        self.check_restriction_to_owners("edit")

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

    def post_update(self):
        if len(self.workflows) == 1 and not self.shared:
            self.path = f"{self.workflows[0].path}>{self.id}"
        else:
            self.path = str(self.id)
        self.set_name()
        return self.to_dict(include=["services", "workflows"])

    def update(self, **kwargs):
        old_disabled_status = self.disabled
        if self.path:
            self.check_restriction_to_owners("edit")
        if self.positions and "positions" in kwargs:
            kwargs["positions"] = {**self.positions, **kwargs["positions"]}
        super().update(**kwargs)
        if self.disabled and not old_disabled_status:
            self.disabled_info = f"Disabled at {vs.get_time()} by {current_user}"
        elif not self.disabled:
            self.disabled_info = ""
        if not kwargs.get("migration_import"):
            self.set_name()
            self.update_last_modified_properties()

    def update_last_modified_properties(self):
        super().update_last_modified_properties()
        for ancestor in self.get_ancestors():
            ancestor.last_modified = self.last_modified
            ancestor.last_modified_by = self.last_modified_by

    def get_ancestors(self):
        def rec(service):
            return {service} | set().union(*(rec(w) for w in service.workflows))

        return rec(self)

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
            workflow.services.append(service)
        service.set_name()
        return service

    @property
    def filename(self):
        return vs.strip_all(self.name)

    def set_name(self, name=None):
        if self.shared:
            workflow = "[Shared] "
        elif not self.workflows:
            workflow = ""
        else:
            workflow = f"[{self.workflows[0].name}] "
        self.name = f"{workflow}{name or self.scoped_name}"

    def neighbors(self, workflow, subtype):
        for edge in self.destinations:
            if edge.subtype == subtype and edge.workflow.name == workflow.name:
                yield edge


class ConnectionService(Service):
    __tablename__ = "connection_service"
    id = db.Column(Integer, ForeignKey("service.id"), primary_key=True)
    parent_type = "service"
    credentials = db.Column(db.SmallString, default="device")
    named_credential_id = db.Column(Integer, ForeignKey("credential.id"))
    named_credential = relationship("Credential")
    custom_username = db.Column(db.SmallString)
    custom_password = db.Column(db.SmallString)
    start_new_connection = db.Column(Boolean, default=False)
    connection_name = db.Column(db.SmallString, default="default")
    close_connection = db.Column(Boolean, default=False)
    __mapper_args__ = {"polymorphic_identity": "connection_service"}


class Result(AbstractBase):
    __tablename__ = type = "result"
    private = True
    log_change = False
    id = db.Column(Integer, primary_key=True)
    path = db.Column(db.SmallString)
    success = db.Column(Boolean, default=False)
    labels = db.Column(db.LargeString)
    runtime = db.Column(db.TinyString)
    duration = db.Column(db.TinyString)
    result = deferred(db.Column(db.Dict))
    creator = db.Column(db.SmallString)
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
        "Device", uselist=False, foreign_keys=device_id, lazy="joined"
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


class ServiceReport(AbstractBase):
    __tablename__ = type = "service_report"
    private = True
    log_change = False
    id = db.Column(Integer, primary_key=True)
    content = db.Column(db.LargeString)
    runtime = db.Column(db.TinyString)
    service_id = db.Column(Integer, ForeignKey("service.id"))
    service = relationship("Service", foreign_keys="ServiceReport.service_id")

    def __repr__(self):
        return f"SERVICE REPORT '{self.service}' ({self.runtime})"


class Run(AbstractBase):
    __tablename__ = type = "run"
    log_change = False
    id = db.Column(Integer, primary_key=True)
    name = db.Column(db.SmallString, unique=True)
    restart_run_id = db.Column(Integer, ForeignKey("run.id", ondelete="SET NULL"))
    restart_run = relationship(
        "Run", remote_side=[id], foreign_keys="Run.restart_run_id"
    )
    start_services = db.Column(db.List)
    creator = db.Column(db.SmallString, default="")
    properties = db.Column(db.Dict)
    payload = deferred(db.Column(db.Dict))
    success = db.Column(Boolean, default=False)
    labels = db.Column(db.LargeString)
    status = db.Column(db.TinyString, default="Running")
    runtime = db.Column(db.TinyString, index=True)
    duration = db.Column(db.TinyString)
    trigger = db.Column(db.TinyString)
    path = db.Column(db.TinyString)
    parameterized_run = db.Column(Boolean, default=False)
    server_id = db.Column(Integer, ForeignKey("server.id"))
    server = relationship("Server", back_populates="runs")
    server_name = association_proxy("server", "name")
    server_version = db.Column(db.TinyString)
    server_commit_sha = db.Column(db.TinyString)
    service_id = db.Column(Integer, ForeignKey("service.id", ondelete="cascade"))
    service = relationship("Service", foreign_keys="Run.service_id", lazy="joined")
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
    start_service_id = db.Column(Integer, ForeignKey("service.id", ondelete="SET NULL"))
    start_service = relationship("Service", foreign_keys="Run.start_service_id")
    task_id = db.Column(Integer, ForeignKey("task.id", ondelete="SET NULL"))
    task = relationship("Task", foreign_keys="Run.task_id")
    task_name = association_proxy("task", "name")
    state = db.Column(db.Dict, info={"log_change": False})
    results = relationship("Result", back_populates="run", cascade="all, delete-orphan")
    model_properties = {
        "progress": "str",
        "server_properties": "dict",
        "service_properties": "dict",
    }

    def __init__(self, **kwargs):
        self.runtime = kwargs.get("runtime") or vs.get_time()
        for property in ("id", "version", "commit_sha"):
            setattr(self, f"server_{property}", getattr(vs, f"server_{property}"))
        super().__init__(**kwargs)
        if not self.name:
            self.name = f"{self.runtime} ({self.creator})"
        self.service_name = (self.placeholder or self.service).scoped_name

    def __repr__(self):
        return f"{self.runtime}: SERVICE '{self.service}'"

    @classmethod
    def rbac_filter(cls, *args):
        return super().rbac_filter(*args, join_class="service")

    @property
    def service_properties(self):
        return self.service.base_properties

    @property
    def server_properties(self):
        return self.server.base_properties

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

    @property
    def progress(self):
        progress = self.get_state().get(str(self.service_id), {}).get("progress")
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
        worker = db.factory("worker", name=str(getpid()), subtype=environ.get("_", "").split("/")[-1])
        env.update_worker_job(self.service.name)
        vs.run_targets[self.runtime] = set(
            device.id
            for device in controller.filtering(
                "device", properties=["id"], rbac="target", username=self.creator
            )
        )
        if not self.trigger:
            run_type = "Parameterized" if self.parameterized_run else "Regular"
            self.trigger = f"{run_type} Run"
        self.service_run = Runner(
            self,
            payload=deepcopy(self.payload),
            service=self.service,
            is_main_run=True,
            restart_run=self.restart_run,
            parameterized_run=self.parameterized_run,
            parent_runtime=self.runtime,
            path=self.path,
            placeholder=self.placeholder,
            properties=self.properties,
            start_services=self.start_services,
            task=self.task,
            trigger=self.trigger,
        )
        self.payload = self.service_run.payload
        db.session.commit()
        vs.run_targets.pop(self.runtime)
        vs.run_services.pop(self.runtime)
        env.update_worker_job(self.service.name, mode="decr")
        return self.service_run.results


class Task(AbstractBase):
    __tablename__ = type = class_type = "task"
    id = db.Column(Integer, primary_key=True)
    name = db.Column(db.SmallString, unique=True)
    admin_only = db.Column(Boolean, default=False)
    description = db.Column(db.LargeString)
    creator = db.Column(db.SmallString)
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
    service_id = db.Column(Integer, ForeignKey("service.id"))
    service = relationship("Service", back_populates="tasks")
    service_name = association_proxy("service", "name")
    model_properties = {
        "next_run_time": "str",
        "time_before_next_run": "str",
        "status": "str",
    }

    def update(self, **kwargs):
        super().update(**kwargs)
        if not kwargs.get("import_mechanism", False):
            db.session.commit()
            self.schedule(mode="schedule" if self.is_active else "pause")

    def delete(self):
        post(f"{env.scheduler_address}/delete_job/{self.id}")

    @hybrid_property
    def status(self):
        return "Active" if self.is_active else "Inactive"

    @status.expression
    def status(cls):  # noqa: N805
        return case((cls.is_active, "Active"), else_="Inactive")

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

    @property
    @_catch_request_exceptions
    def next_run_time(self):
        return get(
            f"{env.scheduler_address}/next_runtime/{self.id}", timeout=0.01
        ).json()

    @property
    @_catch_request_exceptions
    def time_before_next_run(self):
        return get(f"{env.scheduler_address}/time_left/{self.id}", timeout=0.01).json()

    @_catch_request_exceptions
    def schedule(self, mode="schedule"):
        try:
            payload = {"mode": mode, "task": self.get_properties()}
            result = post(f"{env.scheduler_address}/schedule", json=payload).json()
            self.last_scheduled_by = current_user.name
        except ConnectionError:
            return {"alert": "Scheduler Unreachable: the task cannot be scheduled."}
        self.is_active = result.get("active", False)
        return result
