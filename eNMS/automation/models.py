from copy import deepcopy
from datetime import datetime
from json import load
from logging import info
from multiprocessing import Lock
from multiprocessing.pool import ThreadPool
from napalm import get_network_driver
from napalm.base.base import NetworkDriver
from netmiko import ConnectHandler
from os import environ
from paramiko import SSHClient
from re import compile, search
from scp import SCPClient
from sqlalchemy import Boolean, case, Column, ForeignKey, Integer, PickleType, String
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.ext.mutable import MutableDict, MutableList
from sqlalchemy.orm import backref, relationship
from time import sleep
from traceback import format_exc
from typing import Any, List, Optional, Set, Tuple
from xmltodict import parse

from eNMS import controller, db
from eNMS.associations import (
    job_device_table,
    job_log_rule_table,
    job_pool_table,
    job_workflow_table,
)
from eNMS.functions import fetch, session_scope
from eNMS.models import Base
from eNMS.inventory.models import Device


class Job(Base):

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

    def compute_targets(self) -> Set[Device]:
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
        targets: Optional[Set[Device]] = None,
        workflow: Optional["Workflow"] = None,
    ) -> Tuple[dict, str]:
        logs = workflow.logs if workflow else self.logs
        logs.append(f"{self.type} {self.name}: Starting.")
        with session_scope():
            self.is_running, self.state, self.logs = True, {}, []
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
        for i in range(self.number_of_retries + 1):
            logs.append(f"Running {self.type} {self.name} (attempt n°{i + 1})")
            with session_scope():
                self.completed = self.failed = 0
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
        with session_scope():
            self.results[now] = {**results, "logs": logs}
            self.is_running, self.state = False, {}
            self.completed = self.failed = 0
        if not workflow and self.send_notification:
            self.notify(results, now)
        return results, now

    def get_results(
        self,
        payload: dict,
        device: Optional[Device] = None,
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
        self, args: Tuple[Device, dict, dict, Optional["Workflow"], Any]
    ) -> None:
        with controller.app.app_context():
            device, results, payload, workflow, lock = args
            device_result = self.get_results(payload, device, workflow, True)
            with lock:
                with session_scope() as session:
                    session.merge(workflow or self)
                    results["devices"][device.name] = device_result

    def run(
        self,
        payload: dict,
        job_from_workflow_targets: bool,
        targets: Optional[Set[Device]] = None,
        workflow: Optional["Workflow"] = None,
    ) -> dict:
        if job_from_workflow_targets:
            assert targets is not None
            device, = targets
            return self.get_results(payload, device, workflow)
        elif targets:
            results: dict = {"devices": {}}
            if self.multiprocessing:
                lock = Lock()
                processes = min(len(targets), self.max_processes)
                pool = ThreadPool(processes=processes)
                args = (results, payload, workflow, lock)
                pool.map(self.device_run, [(device, *args) for device in targets])
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


class Service(Job):

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
            onclick="editService('{self.id}')">Edit</button>""",
            f"""<button type="button" class="btn btn-primary btn-xs"
            onclick="editService('{self.id}', true)">Duplicate</button>""",
            f"""<button type="button" class="btn btn-danger btn-xs"
            onclick="confirmDeletion('service', '{self.id}')">
            Delete</button>""",
        ]

    def get_credentials(self, device: Device) -> Tuple[str, str]:
        return (
            (self.creator.name, self.creator.password)
            if self.credentials == "user"
            else (device.username, device.password)
        )

    def netmiko_connection(self, device: Device) -> ConnectHandler:
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

    def napalm_connection(self, device: Device) -> NetworkDriver:
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


class WorkflowEdge(Base):

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


class Workflow(Job):

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
            onclick="showTypeModal('workflow', '{self.id}')">
            Edit</button>""",
            f"""<button type="button" class="btn btn-primary btn-xs"
            onclick="showWorkflowModalDuplicate('{self.id}')">
            Duplicate</button>""",
            f"""<button type="button" class="btn btn-danger btn-xs"
            onclick="confirmDeletion('workflow', '{self.id}')">
            Delete</button>""",
        ]

    def job(self, payload: dict, device: Optional[Device] = None) -> dict:
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
