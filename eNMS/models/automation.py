from apscheduler.triggers.cron import CronTrigger
from copy import deepcopy
from datetime import datetime
from git import Repo
from git.exc import GitCommandError
from json import load
from logging import info
from multiprocessing import Manager
from multiprocessing.pool import Pool
from napalm import get_network_driver
from napalm.base.base import NetworkDriver
from netmiko import ConnectHandler
from pathlib import Path
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

from eNMS.concurrent import threaded_job, device_process
from eNMS.controller import controller
from eNMS.database import Session, SMALL_STRING_LENGTH
from eNMS.database.functions import fetch
from eNMS.models.associations import (
    job_device_table,
    job_log_rule_table,
    job_pool_table,
    job_workflow_table,
)
from eNMS.database.base import AbstractBase
from eNMS.models.inventory import Device


class Job(AbstractBase):

    __tablename__ = "Job"
    type = Column(String(SMALL_STRING_LENGTH), default="")
    __mapper_args__ = {"polymorphic_identity": "Job", "polymorphic_on": type}
    id = Column(Integer, primary_key=True)
    hidden = Column(Boolean, default=False)
    name = Column(String(SMALL_STRING_LENGTH), unique=True)
    description = Column(String(SMALL_STRING_LENGTH), default="")
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
    credentials = Column(String(SMALL_STRING_LENGTH), default="device")
    tasks = relationship("Task", back_populates="job", cascade="all,delete")
    vendor = Column(String(SMALL_STRING_LENGTH), default="")
    operating_system = Column(String(SMALL_STRING_LENGTH), default="")
    waiting_time = Column(Integer, default=0)
    creator = Column(String(SMALL_STRING_LENGTH), default="admin")
    push_to_git = Column(Boolean, default=False)
    real_time_update = Column(Boolean, default=False)
    workflows = relationship(
        "Workflow", secondary=job_workflow_table, back_populates="jobs"
    )
    devices = relationship("Device", secondary=job_device_table, back_populates="jobs")
    pools = relationship("Pool", secondary=job_pool_table, back_populates="jobs")
    log_rules = relationship(
        "LogRule", secondary=job_log_rule_table, back_populates="jobs"
    )
    send_notification = Column(Boolean, default=False)
    send_notification_method = Column(
        String(SMALL_STRING_LENGTH), default="mail_feedback_notification"
    )
    display_only_failed_nodes = Column(Boolean, default=True)
    mail_recipient = Column(String(SMALL_STRING_LENGTH), default="")
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
        Session.commit()
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
        server_url = controller.config.get("ENMS_SERVER_ADDR", "http://SERVER_IP")
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

    def git_push(self, results: dict) -> None:
        path_git_folder = Path.cwd() / "git" / "automation"
        with open(path_git_folder / self.name, "w") as file:
            file.write(controller.str_dict(results))
        repo = Repo(str(path_git_folder))
        try:
            repo.git.add(A=True)
            repo.git.commit(m=f"Automatic commit ({self.name})")
        except GitCommandError:
            pass
        repo.remotes.origin.push()

    def try_run(
        self,
        session,
        payload: Optional[dict] = None,
        targets: Optional[Set["Device"]] = None,
        workflow: Optional["Workflow"] = None,
        task: Optional["Task"] = None,
    ) -> Tuple[dict, str]:
        current_job = workflow or self
        self.is_running, self.state = True, {}
        current_job.logs = [f"{self.type} {self.name}: Starting."]
        Session.commit()
        results: dict = {"results": {}}
        if not payload:
            payload = {}
        job_from_workflow_targets = bool(workflow and targets)
        if not targets and getattr(self, "use_workflow_targets", True):
            targets = self.compute_targets()
        has_targets = bool(targets)
        if has_targets and not job_from_workflow_targets:
            results["results"]["devices"] = {}
        now = controller.get_time()
        for i in range(self.number_of_retries + 1):
            current_job.logs.append(
                f"Running {self.type} {self.name} (attempt n°{i + 1})"
            )
            self.completed = self.failed = 0
            Session.commit()
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
        current_job.logs.append(f"{self.type} {self.name}: Finished.")
        self.results[now] = {**results, "logs": list(current_job.logs)}
        current_job.logs = []
        self.is_running, self.state = False, {}
        self.completed = self.failed = 0
        if task and not task.frequency:
            task.is_active = False
        Session.commit()
        if not workflow and self.send_notification:
            self.notify(results, now)
        return results, now

    def get_results(
        self,
        payload: dict,
        device: Optional["Device"] = None,
        workflow: Optional["Workflow"] = None,
    ) -> Tuple[dict, list]:
        logs = []
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
        current_job = workflow or self
        current_job.completed += 1
        current_job.failed += 1 - results["success"]
        current_job.logs.extend(logs)
        if current_job.real_time_update and not current_job.multiprocessing:
            Session.commit()
        return results, logs

    def run(
        self,
        payload: dict,
        job_from_workflow_targets: bool,
        targets: Optional[Set["Device"]] = None,
        workflow: Optional["Workflow"] = None,
    ) -> Tuple[dict, list]:
        if job_from_workflow_targets:
            assert targets is not None
            device, = targets
            return self.get_results(payload, device, workflow)
        elif targets:
            manager = Manager()
            results: dict = manager.dict({"devices": manager.dict()})
            if self.multiprocessing:
                lock = manager.Lock()
                processes = min(len(targets), self.max_processes)
                pool = Pool(processes=processes)
                args = (self.id, lock, results, payload, getattr(workflow, "id", None))
                pool.map(device_process, [(device.id, *args) for device in targets])
                pool.close()
                pool.join()
            else:
                results["devices"] = {
                    device.name: self.get_results(payload, device, workflow)[0]
                    for device in targets
                }
            return results
        else:
            return self.get_results(payload)


class Service(Job):

    __tablename__ = "Service"
    id = Column(Integer, ForeignKey("Job.id"), primary_key=True)
    __mapper_args__ = {"polymorphic_identity": "Service"}
    parent_cls = "Job"

    def generate_row(self, table: str) -> List[str]:
        return [
            f"""<button type="button" class="btn btn-info btn-xs"
            onclick="showLogs('{self.id}')"></i>Logs</a></button>""",
            f"""<button type="button" class="btn btn-info btn-xs"
            onclick="showResultsPanel('{self.id}', '{self.name}')">
            </i>Results</a></button>""",
            f"""<button type="button" class="btn btn-success btn-xs"
            onclick="runJob('{self.id}')">Run</button>""",
            f"""<button type="button" class="btn btn-primary btn-xs"
            onclick="showTypePanel('{self.type}', '{self.id}')">Edit</button>""",
            f"""<button type="button" class="btn btn-primary btn-xs"
            onclick="showTypePanel('{self.type}', '{self.id}', true)">
            Duplicate</button>""",
            f"""<button type="button" class="btn btn-danger btn-xs"
            onclick="showDeletionPanel('service', '{self.id}', '{self.name}')">
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

    def sub_dict(self, input: dict, variables: dict) -> dict:
        return {
            self.sub(k, variables)
            if isinstance(k, str)
            else k: (
                self.sub(v, variables)
                if isinstance(v, str)
                else [self.sub(x, variables) for x in v]
                if isinstance(v, list)
                else self.sub_dict(v, variables)
                if isinstance(v, dict)
                else v
            )
            for k, v in input.items()
        }

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


class Workflow(Job):

    __tablename__ = "Workflow"
    __mapper_args__ = {"polymorphic_identity": "Workflow"}
    parent_cls = "Job"
    id = Column(Integer, ForeignKey("Job.id"), primary_key=True)
    use_workflow_targets = Column(Boolean, default=True)
    last_modified = Column(String(SMALL_STRING_LENGTH), default="")
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
            onclick="showResultsPanel('{self.id}', '{self.name}')">
            </i>Results</a></button>""",
            f"""<button type="button" class="btn btn-success btn-xs"
            onclick="runJob('{self.id}')">Run</button>""",
            f"""<button type="button" class="btn btn-primary btn-xs"
            onclick="showTypePanel('workflow', '{self.id}')">
            Edit</button>""",
            f"""<button type="button" class="btn btn-primary btn-xs"
            onclick="showWorkflowModalDuplicate('{self.id}')">
            Duplicate</button>""",
            f"""<button type="button" class="btn btn-danger btn-xs"
            onclick="showDeletionPanel('workflow', '{self.id}', '{self.name}')">
            Delete</button>""",
        ]

    def job(self, payload: dict, device: Optional["Device"] = None) -> dict:
        self.state = {"jobs": {}}
        if device:
            self.state["current_device"] = device.name
        Session.commit()
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
            Session.commit()
            log = f"Workflow {self.name}: job {job.name}"
            if device:
                log += f" on {device.name}"
            info(log)
            job_results, _ = job.try_run(
                results, {device} if device else None, workflow=self
            )
            success = job_results["results"]["success"]
            self.state["jobs"][job.id] = success
            Session.commit()
            edge_type_to_follow = "success" if success else "failure"
            for successor in job.job_successors(self, edge_type_to_follow):
                if successor not in visited:
                    jobs.append(successor)
                if successor == self.jobs[1]:
                    results["success"] = True
            results[job.name] = job_results
            sleep(job.waiting_time)
        return results


class WorkflowEdge(AbstractBase):

    __tablename__ = type = "WorkflowEdge"
    id = Column(Integer, primary_key=True)
    name = Column(String(SMALL_STRING_LENGTH))
    subtype = Column(String(SMALL_STRING_LENGTH))
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


class Task(AbstractBase):

    __tablename__ = "Task"
    type = "Task"
    id = Column(Integer, primary_key=True)
    aps_job_id = Column(String(SMALL_STRING_LENGTH))
    name = Column(String(SMALL_STRING_LENGTH), unique=True)
    description = Column(String(SMALL_STRING_LENGTH))
    creation_time = Column(String(SMALL_STRING_LENGTH))
    scheduling_mode = Column(String(SMALL_STRING_LENGTH), default="standard")
    periodic = Column(Boolean)
    frequency = Column(Integer)
    frequency_unit = Column(String(SMALL_STRING_LENGTH), default="seconds")
    start_date = Column(String(SMALL_STRING_LENGTH))
    end_date = Column(String(SMALL_STRING_LENGTH))
    crontab_expression = Column(String(SMALL_STRING_LENGTH))
    is_active = Column(Boolean, default=False)
    job_id = Column(Integer, ForeignKey("Job.id"))
    job = relationship("Job", back_populates="tasks")
    job_name = association_proxy("job", "name")

    def __init__(self, **kwargs: Any) -> None:
        super().update(**kwargs)
        self.creation_time = controller.get_time()
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
            onclick="showDeletionPanel('task', '{self.id}', '{self.name}')">
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
        job = controller.scheduler.get_job(self.aps_job_id)
        if job and job.next_run_time:
            return job.next_run_time.strftime("%Y-%m-%d %H:%M:%S")
        return None

    @property
    def time_before_next_run(self) -> Optional[str]:
        job = controller.scheduler.get_job(self.aps_job_id)
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
        controller.scheduler.pause_job(self.aps_job_id)
        self.is_active = False
        Session.commit()

    def resume(self) -> None:
        self.schedule()
        controller.scheduler.resume_job(self.aps_job_id)
        self.is_active = True
        Session.commit()

    def delete_task(self) -> None:
        if controller.scheduler.get_job(self.aps_job_id):
            controller.scheduler.remove_job(self.aps_job_id)
        Session.commit()

    def kwargs(self) -> Tuple[dict, dict]:
        default = {
            "id": self.aps_job_id,
            "func": threaded_job,
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
        if not controller.scheduler.get_job(self.aps_job_id):
            controller.scheduler.add_job(**{**default, **trigger})
        else:
            controller.scheduler.reschedule_job(default.pop("id"), **trigger)
