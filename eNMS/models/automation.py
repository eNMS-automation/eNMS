from collections import defaultdict
from copy import deepcopy
from git import Repo
from git.exc import GitCommandError
from json import loads
from json.decoder import JSONDecodeError
from logging import FileHandler, Formatter, getLogger, INFO
from multiprocessing import Lock, Manager
from multiprocessing.pool import Pool, ThreadPool
from napalm import get_network_driver
from napalm.base.base import NetworkDriver
from netmiko import ConnectHandler
from pathlib import Path
from paramiko import SSHClient
from re import compile, search
from scp import SCPClient
from sqlalchemy import (
    Boolean,
    case,
    Column,
    ForeignKey,
    Integer,
    PickleType,
    String,
    Text,
)
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.ext.mutable import MutableDict, MutableList
from sqlalchemy.orm import backref, relationship
from time import sleep
from traceback import format_exc
from typing import Any, Generator, List, Match, Optional, Set, Tuple, Union
from xmltodict import parse
from xml.parsers.expat import ExpatError
from yaql import factory as yaql_factory

from eNMS.concurrency import device_process, device_thread
from eNMS.controller import controller
from eNMS.database import (
    CustomMediumBlobPickle,
    LARGE_STRING_LENGTH,
    Session,
    SMALL_STRING_LENGTH,
)
from eNMS.database.functions import factory, fetch
from eNMS.database.associations import (
    job_device_table,
    job_event_table,
    job_pool_table,
    job_workflow_table,
)
from eNMS.database.base import AbstractBase
from eNMS.exceptions import VariableSubstitutionError
from eNMS.models.inventory import Device
from eNMS.models.events import Task  # noqa: F401


class Result(AbstractBase):

    __tablename__ = type = "Result"
    id = Column(Integer, primary_key=True)
    timestamp = Column(String(SMALL_STRING_LENGTH), default="")
    parent_timestamp = Column(String(SMALL_STRING_LENGTH), default="")
    result = Column(MutableDict.as_mutable(PickleType), default={})
    job_id = Column(Integer, ForeignKey("Job.id"))
    job = relationship("Job", back_populates="results", foreign_keys="Result.job_id")
    job_name = association_proxy("job", "name")
    device_id = Column(Integer, ForeignKey("Device.id"))
    device = relationship(
        "Device", back_populates="results", foreign_keys="Result.device_id"
    )
    device_name = association_proxy("device", "name")
    workflow_id = Column(Integer, ForeignKey("Workflow.id"))
    workflow = relationship("Workflow", foreign_keys="Result.workflow_id")

    def __repr__(self):
        return f"{self.job_name} ({self.timestamp})"

    @property
    def name(self):
        return repr(self)


class Job(AbstractBase):

    __tablename__ = "Job"
    type = Column(String(SMALL_STRING_LENGTH), default="")
    __mapper_args__ = {"polymorphic_identity": "Job", "polymorphic_on": type}
    id = Column(Integer, primary_key=True)
    hidden = Column(Boolean, default=False)
    name = Column(String(SMALL_STRING_LENGTH), unique=True)
    last_modified = Column(String(SMALL_STRING_LENGTH), default="")
    description = Column(String(SMALL_STRING_LENGTH), default="")
    number_of_retries = Column(Integer, default=0)
    time_between_retries = Column(Integer, default=10)
    positions = Column(MutableDict.as_mutable(PickleType), default={})
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
    workflows = relationship(
        "Workflow", secondary=job_workflow_table, back_populates="jobs"
    )
    define_devices_from_payload = Column(Boolean, default=False)
    yaql_query = Column(String(SMALL_STRING_LENGTH), default="")
    query_property_type = Column(String(SMALL_STRING_LENGTH), default="ip_address")
    devices = relationship("Device", secondary=job_device_table, back_populates="jobs")
    pools = relationship("Pool", secondary=job_pool_table, back_populates="jobs")
    events = relationship("Event", secondary=job_event_table, back_populates="jobs")
    send_notification = Column(Boolean, default=False)
    send_notification_method = Column(
        String(SMALL_STRING_LENGTH), default="mail_feedback_notification"
    )
    notification_header = Column(Text(LARGE_STRING_LENGTH), default="")
    display_only_failed_nodes = Column(Boolean, default=True)
    include_link_in_summary = Column(Boolean, default=True)
    mail_recipient = Column(String(SMALL_STRING_LENGTH), default="")
    shape = Column(String(SMALL_STRING_LENGTH), default="box")
    size = Column(Integer, default=40)
    color = Column(String(SMALL_STRING_LENGTH), default="#D2E5FF")
    initial_payload = Column(MutableDict.as_mutable(PickleType), default={})
    custom_username = Column(String(SMALL_STRING_LENGTH), default="")
    custom_password = Column(String(SMALL_STRING_LENGTH), default="")
    results = relationship("Result", back_populates="job")

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.configure_logger()

    def configure_logger(self) -> None:
        logger = getLogger(self.name)
        logger.setLevel(INFO)
        filename = f"{controller.strip_all(self.name)}.log"
        fh = FileHandler(controller.path / "logs" / "job_logs" / filename)
        formatter = Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    @hybrid_property
    def status(self) -> str:
        return "Running" if self.is_running else "Idle"

    @status.expression  # type: ignore
    def status(cls) -> str:  # noqa: N805
        return case([(cls.is_running, "Running")], else_="Idle")

    @property
    def progress(self) -> str:
        if self.is_running and not getattr(self, "multiprocessing", False):
            return f"{self.completed}/{self.number_of_targets} ({self.failed} failed)"
        else:
            return "N/A"

    def compute_devices(self, payload: Optional[dict] = None) -> Set["Device"]:
        if self.define_devices_from_payload:
            engine = yaql_factory.YaqlFactory().create()
            devices = {
                fetch("Device", **{self.query_property_type: value})
                for value in engine(self.yaql_query).evaluate(data=payload)
            }
        else:
            devices = set(self.devices)
            for pool in self.pools:
                devices |= set(pool.devices)
            self.number_of_targets = len(devices)
            Session.commit()
        return devices

    def adjacent_jobs(
        self, workflow: "Workflow", direction: str, subtype: str
    ) -> Generator["Job", None, None]:
        for x in getattr(self, f"{direction}s"):
            if x.subtype == subtype and x.workflow == workflow:
                yield getattr(x, direction)

    def notify(self, results: dict, time: str) -> None:
        notification = [
            f"Job: {self.name} ({self.type})",
            f"Runtime: {time}",
            f'Status: {"PASS" if results["success"] else "FAILED"}',
        ]
        notification.extend(self.job_notification(results))
        if self.include_link_in_summary:
            notification.append(
                f"Results: {controller.enms_server_addr}/view_job_results"
                f"/{self.id}/{time.replace(' ', '$')}"
            )
        fetch("Job", name=self.send_notification_method).run(
            {
                "job": self.get_properties(),
                "results": results,
                "runtime": time,
                "result": results["success"],
                "content": "\n\n".join(notification),
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

    def log(self, parent, severity, log: str) -> None:
        getattr(getLogger(self.name), severity)(log)
        if parent:
            getattr(getLogger(parent.name), severity)(log)

    def run(
        self,
        payload: Optional[dict] = None,
        targets: Optional[Set["Device"]] = None,
        parent: Optional["Job"] = None,
        parent_timestamp: Optional[str] = None,
        task: Optional["Task"] = None,
        origin: Optional["Job"] = None,
    ) -> Tuple[dict, str]:
        runtime = controller.get_time()
        if not parent_timestamp:
            parent_timestamp = runtime
        self.is_running, self.state = True, {}
        self.log(parent, "info", f"{self.type} {self.name}: Starting.")
        if not parent:
            Session.commit()
        results = self.build_results(
            runtime, payload, targets, parent, parent_timestamp, origin
        )
        results
        for library in ("netmiko", "napalm"):
            connections = controller.connections_cache[library].pop(self.name, None)
            if not connections:
                continue
            for device, conn in connections.items():
                self.log(parent, "info", f"Closing Netmiko Connection to {device}")
                conn.disconnect() if library == "netmiko" else conn.close()
        self.log(parent, "info", f"{self.type} {self.name}: Finished.")
        self.is_running, self.state = False, {}
        self.completed = self.failed = 0
        if task and not task.frequency:
            task.is_active = False
        results["properties"] = self.to_dict(True)
        results_kwargs = {"timestamp": runtime, "result": results, "job": self.id}
        if parent:
            results_kwargs["workflow"] = parent.id
            results_kwargs["parent_timestamp"] = parent_timestamp
        factory("Result", **results_kwargs)
        Session.commit()
        if not parent and self.send_notification:
            self.notify(results, runtime)
        return results, runtime


class Service(Job):

    __tablename__ = "Service"
    __mapper_args__ = {"polymorphic_identity": "Service"}
    parent_cls = "Job"
    id = Column(Integer, ForeignKey("Job.id"), primary_key=True)
    multiprocessing = Column(Boolean, default=False)
    max_processes = Column(Integer, default=5)

    def job_notification(self, results: dict) -> List[str]:
        notification = self.notification_header.splitlines()
        if "devices" in results["results"] and not results["success"]:
            failed = "\n".join(
                device
                for device, device_results in results["results"]["devices"].items()
                if not device_results["success"]
            )
            notification.append(f"FAILED :\n{failed}")
            if not self.display_only_failed_nodes:
                passed = "\n".join(
                    device
                    for device, device_results in results["results"]["devices"].items()
                    if device_results["success"]
                )
                notification.append(f"\n\nPASS :\n{passed}")
        return notification

    def get_results(
        self,
        runtime: str,
        payload: dict,
        device: Optional["Device"] = None,
        parent: Optional["Job"] = None,
        parent_timestamp: Optional[str] = None,
    ) -> Tuple[dict, list]:
        kwargs = {"timestamp": runtime, "job": self.id}
        if parent:
            kwargs.update(workflow=parent.id, parent_timestamp=parent_timestamp)
        if device:
            kwargs["device"] = device.id
        self.log(parent, "info", f"Running {self.type} {f'on {device.name}.' if device else '.'}")
        try:
            if device:
                results = self.job(payload, device, parent)
            else:
                results = self.job(payload, parent)
        except Exception:
            results = {
                "success": False,
                "result": chr(10).join(format_exc().splitlines()),
            }
        self.log(parent, "info", 
            f"Finished running {self.type} '{self.name}'"
            f"({'SUCCESS' if results['success'] else 'FAILURE'})"
            f" on {device.name}."
            if device
            else "."
        )
        result = factory("Result", result=results, **kwargs)
        if not parent and not self.multiprocessing:
            self.completed += 1
            self.failed += 1 - results["success"]
            Session.commit()
        return results

    def device_run(
        self,
        runtime: str,
        payload: dict,
        targets: Optional[Set["Device"]] = None,
        parent: Optional["Job"] = None,
        parent_timestamp: Optional[str] = None,
    ) -> Tuple[dict, list]:
        if not targets:
            return self.get_results(runtime, payload)
        else:
            if self.multiprocessing == "multiprocessing":
                manager = Manager()
                device_results: dict = manager.dict()
                lock = manager.Lock()
                processes = min(len(targets), self.max_processes)
                args = (
                    self.id,
                    lock,
                    device_results,
                    runtime,
                    payload,
                    getattr(parent, "id", None),
                    parent_timestamp,
                )
                process_args = [(device.id, *args) for device in targets]
                pool = Pool(processes=processes)
                pool.map(device_process, process_args)
                pool.close()
                pool.join()
                results = {"devices": device_results}
            elif self.multiprocessing:
                device_results = {}
                thread_lock = Lock()
                processes = min(len(targets), self.max_processes)
                args = (  # type: ignore
                    self.id,
                    thread_lock,
                    device_results,
                    runtime,
                    payload,
                    getattr(parent, "id", None),
                    parent_timestamp,
                )
                process_args = [(device.id, *args) for device in targets]
                pool = ThreadPool(processes=processes)
                pool.map(device_thread, process_args)
                pool.close()
                pool.join()
                results = {"devices": device_results}
            else:
                results = {"devices": {}}
                results["devices"] = {
                    device.name: self.get_results(
                        runtime, payload, device, parent, parent_timestamp
                    )
                    for device in targets
                }
            return results

    def build_results(
        self,
        runtime: str,
        payload: Optional[dict] = None,
        targets: Optional[Set["Device"]] = None,
        parent: Optional["Job"] = None,
        parent_timestamp: Optional[str] = None,
        *other: Any,
    ) -> dict:
        results: dict = {"results": {}, "success": False}
        if self.has_targets and not targets:
            targets = self.compute_devices(payload)
        if targets:
            results["results"]["devices"] = {}
        for i in range(self.number_of_retries + 1):
            self.log(parent, "info", f"Running {self.type} {self.name} (attempt n°{i + 1})")
            self.completed = self.failed = 0
            if not parent:
                Session.commit()
            attempt = self.device_run(
                runtime, payload or {}, targets, parent, parent_timestamp
            )
            Session.commit()
            if targets:
                assert targets is not None
                for device in set(targets):
                    if not attempt["devices"][device.name]["success"]:
                        continue
                    results["results"]["devices"][device.name] = attempt["devices"][
                        device.name
                    ]
                    targets.remove(device)
                if not targets:
                    results["success"] = True
                    break
                else:
                    if self.number_of_retries:
                        results[f"Attempt {i + 1}"] = attempt
                    if i != self.number_of_retries:
                        sleep(self.time_between_retries)
                    else:
                        for device in targets:
                            results["results"]["devices"][device.name] = attempt[
                                "devices"
                            ][device.name]
            else:
                if self.number_of_retries:
                    results[f"Attempts {i + 1}"] = attempt
                if attempt["success"] or i == self.number_of_retries:
                    results["results"] = attempt
                    results["success"] = attempt["success"]
                    break
                else:
                    sleep(self.time_between_retries)
        return results

    def generate_row(self, table: str) -> List[str]:
        return [
            f"""<button type="button" class="btn btn-info btn-xs"
            onclick="showLogHistory('{self.id}', '{self.name}')"></i>Logs</a></button>""",
            f"""<button type="button" class="btn btn-info btn-xs"
            onclick="showResultsPanel('{self.id}', '{self.name}')">
            </i>Results</a></button>""",
            f"""<button type="button" class="btn btn-success btn-xs"
            onclick="runJob('{self.id}', '{self.name}')">Run</button>""",
            f"""<button type="button" class="btn btn-primary btn-xs"
            onclick="showTypePanel('{self.type}', '{self.id}')">Edit</button>""",
            f"""<button type="button" class="btn btn-primary btn-xs"
            onclick="showTypePanel('{self.type}', '{self.id}', true)">
            Duplicate</button>""",
            f"""<button type="button" class="btn btn-primary btn-xs"
            onclick="exportJob('{self.id}')">
            Export</button>""",
            f"""<button type="button" class="btn btn-danger btn-xs"
            onclick="showDeletionPanel('service', '{self.id}', '{self.name}')">
            Delete</button>""",
        ]

    def get_credentials(self, device: "Device") -> Tuple[str, str]:
        return (
            controller.get_user_credentials()
            if self.credentials == "user"
            else (device.username, device.password)
            if self.credentials == "device"
            else (
                self.sub(self.custom_username, locals()),
                self.sub(self.custom_password, locals()),
            )
        )

    def netmiko_connection(self, device: "Device", parent: "Job") -> ConnectHandler:
        if getattr(parent, "name", None) in controller.connections_cache["netmiko"]:
            parent_connection = controller.connections_cache["netmiko"].get(parent.name)
            if parent_connection and device.name in parent_connection:
                try:
                    parent_connection[device.name].find_prompt()
                    return parent_connection[device.name]
                except ValueError:
                    parent_connection.pop(device.name)
        username, password = self.get_credentials(device)
        netmiko_connection = ConnectHandler(
            device_type=(
                device.netmiko_driver if self.use_device_driver else self.driver
            ),
            ip=device.ip_address,
            port=getattr(device, "port"),
            username=username,
            password=password,
            secret=device.enable_password,
            fast_cli=self.fast_cli,
            timeout=self.timeout,
            global_delay_factor=self.global_delay_factor,
        )
        if self.privileged_mode:
            netmiko_connection.enable()
        if parent:
            controller.connections_cache["netmiko"][parent.name][
                device.name
            ] = netmiko_connection
        return netmiko_connection

    def napalm_connection(self, device: "Device", parent: "Job") -> NetworkDriver:
        if getattr(parent, "name", None) in controller.connections_cache["napalm"]:
            parent_connection = controller.connections_cache["napalm"].get(parent.name)
            if parent_connection and device.name in parent_connection:
                if parent_connection[device.name].is_alive():
                    return parent_connection[device.name]
                else:
                    parent_connection.pop(device.name)
        username, password = self.get_credentials(device)
        optional_args = self.optional_args
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
            optional_args=optional_args,
        )
        napalm_connection.open()
        if parent:
            controller.connections_cache["napalm"][parent.name][
                device.name
            ] = napalm_connection
        return napalm_connection

    def space_deleter(self, input: str) -> str:
        return "".join(input.split())

    def convert_result(self, result: Any) -> Union[str, dict]:
        try:
            if self.conversion_method == "json":
                result = loads(result)
            elif self.conversion_method == "xml":
                result = parse(result)
        except (ExpatError, JSONDecodeError) as e:
            result = {
                "success": False,
                "text_response": result,
                "error": f"Conversion to {self.conversion_method} failed",
                "exception": str(e),
            }
        return result

    def match_content(self, result: Any, match: Union[str, dict]) -> bool:
        if getattr(self, "validation_method", "text") == "text":
            result = str(result)
            assert isinstance(match, str)
            if self.delete_spaces_before_matching:
                match, result = map(self.space_deleter, (match, result))
            success = (
                self.content_match_regex
                and bool(search(match, result))
                or match in result
                and not self.content_match_regex
            )
        else:
            assert isinstance(match, dict)
            success = self.match_dictionary(result, match)
        return success if not self.negative_logic else not success

    def sub(self, input: Any, variables: dict) -> dict:
        r = compile("{{(.*?)}}")

        def replace(match: Match) -> str:
            try:
                return str(eval(match.group()[2:-2], variables))
            except AttributeError:
                raise VariableSubstitutionError(
                    "The variable subtitution mechanism failed."
                    " If you are using the 'device' variable, "
                    "check that the service has targets."
                )
            except NameError:
                raise VariableSubstitutionError(
                    "The variable subtitution mechanism failed."
                    " Check that all variables are defined."
                )

        def rec(input: Any) -> Any:
            if isinstance(input, str):
                return r.sub(replace, input)
            elif isinstance(input, list):
                return [rec(x) for x in input]
            elif isinstance(input, dict):
                return {rec(k): rec(v) for k, v in input.items()}
            else:
                return input

        return rec(input)

    def match_dictionary(self, result: dict, match: dict) -> bool:
        if self.validation_method == "dict_equal":
            return result == self.dict_match
        else:
            match_copy = deepcopy(match)
            for k, v in result.items():
                if isinstance(v, dict):
                    self.match_dictionary(v, match_copy)
                elif k in match_copy and match_copy[k] == v:
                    match_copy.pop(k)
            return not match_copy

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
    has_targets = Column(Boolean, default=True)
    id = Column(Integer, ForeignKey("Job.id"), primary_key=True)
    use_workflow_targets = Column(Boolean, default=True)
    jobs = relationship("Job", secondary=job_workflow_table, back_populates="workflows")
    edges = relationship("WorkflowEdge", back_populates="workflow")

    def __init__(self, **kwargs: Any) -> None:
        end = fetch("Service", name="End")
        default = [fetch("Service", name="Start"), end]
        self.jobs.extend(default)
        super().__init__(**kwargs)
        if self.name not in end.positions:
            end.positions[self.name] = (500, 0)

    def job_notification(self, results: dict) -> list:
        return self.notification_header.splitlines()

    def generate_row(self, table: str) -> List[str]:
        return [
            f"""<button type="button" class="btn btn-info btn-xs"
            onclick="showLogHistory('{self.id}', '{self.name}')"></i>Logs</a></button>""",
            f"""<button type="button" class="btn btn-info btn-xs"
            onclick="showResultsPanel('{self.id}', '{self.name}', true)">
            </i>Results</a></button>""",
            f"""<button type="button" class="btn btn-success btn-xs"
            onclick="runJob('{self.id}', '{self.name}')">Run</button>""",
            f"""<button type="button" class="btn btn-primary btn-xs"
            onclick="showTypePanel('workflow', '{self.id}')">
            Edit</button>""",
            f"""<button type="button" class="btn btn-primary btn-xs"
            onclick="showTypePanel('workflow', '{self.id}', true)">
            Duplicate</button>""",
            f"""<button type="button" class="btn btn-primary btn-xs"
            onclick="exportJob('{self.id}')">
            Export</button>""",
            f"""<button type="button" class="btn btn-danger btn-xs"
            onclick="showDeletionPanel('workflow', '{self.id}', '{self.name}')">
            Delete</button>""",
        ]

    def compute_valid_devices(
        self, job: Job, allowed_devices: dict, payload: Optional[dict] = None
    ) -> Set[Device]:
        if job.type != "Workflow" and not job.has_targets:
            return set()
        elif self.use_workflow_targets:
            return allowed_devices[job.name]
        else:
            return job.compute_devices(payload)

    def workflow_targets_processing(
        self, allowed_devices: dict, job: Job, results: dict
    ) -> Generator[Job, None, None]:
        failed_devices, passed_devices = set(), set()
        if job.type == "Workflow" or job.has_targets:
            if job.type == "Workflow":
                devices = results["devices"]
            else:
                devices = results["results"].get("devices", {})
            for name, device_results in devices.items():
                if device_results["success"]:
                    passed_devices.add(fetch("Device", name=name))
                else:
                    failed_devices.add(fetch("Device", name=name))
        else:
            if results["success"]:
                passed_devices = allowed_devices[job.name]
            else:
                failed_devices = allowed_devices[job.name]
        for devices, edge in ((passed_devices, "success"), (failed_devices, "failure")):
            if not devices:
                continue
            for successor in job.adjacent_jobs(self, "destination", edge):
                allowed_devices[successor.name] |= devices
                yield successor

    def build_results(
        self,
        runtime,
        payload: Optional[dict] = None,
        targets: Optional[Set["Device"]] = None,
        parent: Optional["Job"] = None,
        parent_timestamp: Optional[str] = None,
        origin: Optional["Job"] = None,
    ) -> dict:
        self.state = {"jobs": {}}
        start_job = origin or self.jobs[0]
        jobs: list = [start_job]
        visited: Set = set()
        results: dict = {"results": payload or {}, "success": False}
        allowed_devices: dict = defaultdict(set)
        if self.use_workflow_targets:
            allowed_devices[start_job.name] = targets or self.compute_devices(payload)
        while jobs:
            job = jobs.pop()
            if any(
                node not in visited
                for node in job.adjacent_jobs(self, "source", "prerequisite")
            ):
                continue
            visited.add(job)
            self.state["current_job"] = job.get_properties()
            Session.commit()
            valid_devices = self.compute_valid_devices(
                job, allowed_devices, results["results"]
            )
            job_results, _ = job.run(
                results["results"],
                targets=valid_devices,
                parent=self,
                parent_timestamp=parent_timestamp,
            )
            self.state["jobs"][job.id] = job_results["success"]
            if self.use_workflow_targets:
                successors = self.workflow_targets_processing(
                    allowed_devices, job, job_results
                )
            else:
                successors = job.adjacent_jobs(
                    self,
                    "destination",
                    "success" if job_results["success"] else "failure",
                )
            if job.type == "Workflow":
                job_results.pop("results")
            results["results"][job.name] = job_results
            for successor in successors:
                if successor not in visited:
                    jobs.append(successor)
                if not self.use_workflow_targets and successor == self.jobs[1]:
                    results["success"] = True
            sleep(job.waiting_time)
        if self.use_workflow_targets:
            start_devices = allowed_devices[start_job.name]
            end_devices = allowed_devices["End"]
            results["devices"] = {
                device.name: {"success": device in end_devices}
                for device in start_devices
            }
            results["success"] = start_devices == end_devices
        return results


class WorkflowEdge(AbstractBase):

    __tablename__ = type = "WorkflowEdge"
    id = Column(Integer, primary_key=True)
    name = Column(String(SMALL_STRING_LENGTH), default="")
    subtype = Column(String(SMALL_STRING_LENGTH), default="")
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
