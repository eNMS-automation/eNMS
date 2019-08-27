from collections import defaultdict
from copy import deepcopy
from functools import partial
from git import Repo
from git.exc import GitCommandError
from json import loads
from json.decoder import JSONDecodeError
from multiprocessing import Lock
from multiprocessing.pool import ThreadPool
from napalm import get_network_driver
from napalm.base.base import NetworkDriver
from netmiko import ConnectHandler
from pathlib import Path
from paramiko import SSHClient
from re import compile, search
from scp import SCPClient
from sqlalchemy import Boolean, ForeignKey, Integer
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import backref, relationship
from time import sleep
from traceback import format_exc
from typing import Any, Dict, Generator, List, Match, Optional, Set, Tuple, Union
from xmltodict import parse
from xml.parsers.expat import ExpatError

from eNMS import app
from eNMS.database import Session
from eNMS.database.dialect import (
    Column,
    LargeString,
    MutableDict,
    SmallString,
)
from eNMS.database.functions import convert_value, factory, fetch
from eNMS.database.associations import (
    job_device_table,
    job_event_table,
    job_pool_table,
    job_workflow_table,
    start_jobs_workflow_table,
)
from eNMS.database.base import AbstractBase
from eNMS.models.inventory import Device
from eNMS.models.events import Task  # noqa: F401
from eNMS.models.administration import User  # noqa: F401


class Result(AbstractBase):

    __tablename__ = type = "Result"
    private = True
    id = Column(Integer, primary_key=True)
    success = Column(Boolean, default=False)
    result = Column(MutableDict)
    run_id = Column(Integer, ForeignKey("Run.id"))
    run = relationship("Run", back_populates="results", foreign_keys="Result.run_id")
    device_id = Column(Integer, ForeignKey("Device.id"))
    device = relationship(
        "Device", back_populates="results", foreign_keys="Result.device_id"
    )
    device_name = association_proxy("device", "name")

    def __getitem__(self, key: Any) -> Any:
        return self.result[key]

    def __init__(self, **kwargs: Any) -> None:
        self.success = kwargs["result"]["success"]
        super().__init__(**kwargs)

    def __repr__(self) -> str:
        return f"{self.run} {self.device_name}"


class Run(AbstractBase):

    __tablename__ = type = "Run"
    private = True
    id = Column(Integer, primary_key=True)
    creator = Column(SmallString, default="admin")
    properties = Column(MutableDict)
    success = Column(Boolean, default=False)
    status = Column(SmallString, default="Running")
    runtime = Column(SmallString)
    endtime = Column(SmallString)
    workflow_device_id = Column(Integer, ForeignKey("Device.id"))
    workflow_device = relationship("Device", foreign_keys="Run.workflow_device_id")
    parent_runtime = Column(SmallString)
    restart_runtime = Column(SmallString)
    job_id = Column(Integer, ForeignKey("Job.id"))
    job = relationship("Job", back_populates="runs", foreign_keys="Run.job_id")
    job_name = association_proxy("job", "name")
    workflow_id = Column(Integer, ForeignKey("Workflow.id"))
    workflow = relationship("Workflow", foreign_keys="Run.workflow_id")
    workflow_name = association_proxy("workflow", "name")
    task_id = Column(Integer, ForeignKey("Task.id"))
    task = relationship("Task", foreign_keys="Run.task_id")
    results = relationship("Result", back_populates="run", cascade="all, delete-orphan")

    def __init__(self, **kwargs: Any) -> None:
        self.runtime = kwargs.get("runtime") or app.get_time()  # type: ignore
        if not kwargs.get("parent_runtime"):
            self.parent_runtime = self.runtime
        super().__init__(**kwargs)

    def __repr__(self) -> str:
        return f"{self.runtime} ({self.job_name} run by {self.creator})"

    def __getattr__(self, key: str) -> Any:
        if key in self.__dict__:
            return self.__dict__[key]
        elif key in self.__dict__.get("properties", {}):
            job, value = self.__dict__.get("job"), self.__dict__["properties"][key]
            return convert_value(job.type, key, value, "id") if job else value
        elif self.__dict__.get("job_id"):
            return getattr(self.job, key)
        else:
            raise AttributeError

    def result(self, device: Optional[str] = None) -> Optional["Result"]:
        result = [r for r in self.results if r.device_name == device]
        return result.pop() if result else None

    def generate_row(self, table: str) -> List[str]:
        job_type = "workflow" if self.job.type == "Workflow" else "service"
        return [
            f"""<button type="button" class="btn btn-info btn-xs"
            onclick="showLogsPanel({self.job.row_properties}, '{self.runtime}')">
            </i>Logs</a></button>""",
            f"""<button type="button" class="btn btn-info btn-xs"
            onclick="showResultsPanel('{self.job.id}', '{self.name}',
            '{job_type}', '{self.runtime}')">
            </i>Results</a></button>""",
        ]

    @property
    def progress(self) -> str:
        if self.status == "Running":
            progress = app.run_db[self.runtime]
            try:
                return (
                    f"{progress['completed']}/{progress['number_of_targets']}"
                    f" ({progress['failed']} failed)"
                )
            except KeyError:
                return "N/A"
        else:
            return "N/A"

    def netmiko_connection(self, device: "Device") -> ConnectHandler:
        if self.parent_runtime in app.connections_cache["netmiko"]:
            parent_connection = app.connections_cache["netmiko"].get(
                self.parent_runtime
            )
            if parent_connection and device.name in parent_connection:
                if self.job.start_new_connection:
                    parent_connection.pop(device.name).disconnect()
                else:
                    try:
                        connection = parent_connection[device.name]
                        connection.find_prompt()
                        for property in ("fast_cli", "timeout", "global_delay_factor"):
                            setattr(connection, property, getattr(self.job, property))
                        return connection
                    except (OSError, ValueError):
                        parent_connection.pop(device.name)
        username, password = self.get_credentials(device)
        driver = device.netmiko_driver if self.use_device_driver else self.driver
        netmiko_connection = ConnectHandler(
            device_type=driver,
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
        app.connections_cache["netmiko"][self.parent_runtime][
            device.name
        ] = netmiko_connection
        return netmiko_connection

    def napalm_connection(self, device: "Device") -> NetworkDriver:
        if self.parent_runtime in app.connections_cache["napalm"]:
            parent_connection = app.connections_cache["napalm"].get(self.parent_runtime)
            if parent_connection and device.name in parent_connection:
                if (
                    self.job.start_new_connection
                    or not parent_connection[device.name].is_alive()
                ):
                    parent_connection.pop(device.name).close()
                else:
                    return parent_connection[device.name]
        username, password = self.get_credentials(device)
        optional_args = self.job.optional_args
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
        app.connections_cache["napalm"][self.parent_runtime][
            device.name
        ] = napalm_connection
        return napalm_connection

    def get_state(self, property: str) -> Any:
        return app.run_db[self.runtime][property]

    def set_state(self, **kwargs: Any) -> None:
        app.run_db[self.runtime].update(**kwargs)
        if self.workflow:
            app.run_db[self.parent_runtime]["jobs"][self.job.id].update(**kwargs)
            if "success" in kwargs:
                key = "passed" if kwargs["success"] else "failed"
                app.run_db[self.parent_runtime]["progress"][key] += 1

    def compute_devices(self, payload: dict) -> Set["Device"]:
        if self.job.python_query:
            values = self.eval(self.job.python_query, **locals())
            devices, not_found = [], []
            if isinstance(values, str):
                values = [values]
            for value in values:
                device = fetch(
                    "Device", allow_none=True, **{self.job.query_property_type: value}
                )
                if device:
                    devices.append(device)
                else:
                    not_found.append(value)
            if not_found:
                raise Exception(f"Python query invalid targets: {', '.join(not_found)}")
        else:
            devices = set(self.devices)  # type: ignore
            for pool in self.pools:
                devices |= set(pool.devices)  # type: ignore
        self.set_state(number_of_targets=len(devices))
        return devices  # type: ignore

    def close_connection_cache(self) -> None:
        for library in ("netmiko", "napalm"):
            connections = app.connections_cache[library].pop(self.runtime, None)
            if not connections:
                continue
            for device, conn in connections.items():
                self.log("info", f"Closing {library} Connection to {device}")
                conn.disconnect() if library == "netmiko" else conn.close()

    def run(self, payload: Optional[dict] = None) -> dict:
        try:
            self.log("info", f"{self.job.type} {self.job.name}: Starting")
            self.set_state(status="Running", type=self.job.type)
            app.job_db[self.job.id]["runs"] += 1
            Session.commit()
            results = self.job.build_results(self, payload or self.initial_payload)
            self.close_connection_cache()
        except Exception:
            result = (
                f"Running {self.job.type} '{self.job.name}'"
                " raised the following exception:\n"
                f"{chr(10).join(format_exc().splitlines())}\n\n"
                "Run aborted..."
            )
            self.log("error", result)
            results = {"success": False, "results": result}
        finally:
            status = f"Completed ({'success' if results['success'] else 'failure'})"
            self.status = status  # type: ignore
            self.set_state(status=status, success=results["success"])
            app.job_db[self.job.id]["runs"] -= 1
            results["endtime"] = self.endtime = app.get_time()  # type: ignore
            results["state"] = app.run_db.pop(self.runtime)
            results["logs"] = app.run_logs.pop(self.runtime)  # type: ignore
            if self.task and not self.task.frequency:
                self.task.is_active = False
            results["properties"] = {
                "run": self.properties,
                "service": self.job.to_dict(True),
            }
            self.create_result(results)
            self.log("info", f"{self.job.type} {self.job.name}: Finished")
            Session.commit()
        if not self.workflow and self.send_notification:
            self.notify(results)
        return results

    def create_result(self, results: dict, device: Optional["Device"] = None) -> None:
        self.success = results["success"]
        result_kw = {"run": self, "result": results}
        if device:
            result_kw["device"] = device.id
        factory("Result", **result_kw)

    def get_results(self, payload: dict, device: Optional["Device"] = None) -> dict:
        self.log(
            "info", f"Running {self.job.type}{f' on {device.name}' if device else ''}"
        )
        results: Dict[Any, Any] = {"runtime": app.get_time()}
        try:
            args = (device,) if device else ()
            if self.job.iteration_values:
                targets_results = {
                    target: self.job.job(
                        self,
                        {**payload, self.job.iteration_variable_name: target},
                        *args,
                    )
                    for target in self.eval(self.job.iteration_values, **locals())
                }
                results.update(
                    {
                        "results": targets_results,
                        "success": all(r["success"] for r in targets_results.values()),
                    }
                )
            else:
                results.update(self.job.job(self, payload, *args))
        except Exception:
            results.update(
                {"success": False, "result": chr(10).join(format_exc().splitlines())}
            )
        if self.success_query:
            query_result = self.eval(self.success_query, **locals())
            results.update(
                {"success": query_result, "success_query": self.success_query}
            )
        self.log(
            "info",
            f"Finished running {self.job.type} '{self.job.name}'"
            f"({'SUCCESS' if results['success'] else 'FAILURE'})"
            f"{f' on {device.name}' if device else ''}",
        )
        completed, failed = self.get_state("completed"), self.get_state("failed")
        self.set_state(failed=failed + 1 - results["success"], completed=completed + 1)
        return results

    def log(self, severity: str, log: str) -> None:
        log = f"{app.get_time()} - {severity} - {log}"
        app.run_logs[self.runtime].append(log)
        if self.workflow:
            app.run_logs[self.parent_runtime].append(log)

    def run_notification(self, results: dict) -> List[str]:
        notification = self.notification_header.splitlines()
        if self.job.type == "Workflow":
            return notification
        elif "devices" in results["results"] and not results["success"]:
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

    def notify(self, results: dict) -> None:
        notification = [
            f"Job: {self.job.name} ({self.job.type})",
            f"Runtime: {self.runtime}",
            f'Status: {"PASS" if results["success"] else "FAILED"}',
        ]
        notification.extend(self.run_notification(results))
        if self.include_link_in_summary:
            notification.append(
                f"Results: {app.server_addr}/view_job_results/{self.id}"
            )
        notification_payload = {
            "job": self.job.get_properties(),
            "run": self.properties,
            "results": results,
            "content": "\n\n".join(notification),
        }
        notification_run = factory(
            "Run", **{"job": fetch("Job", name=self.send_notification_method).id}
        )
        notification_run.run(notification_payload)

    def get_credentials(self, device: "Device") -> Tuple:
        return (
            app.get_user_credentials()
            if self.credentials == "user"
            else (device.username, device.password)
            if self.credentials == "device"
            else (
                self.sub(self.job.custom_username, locals()),
                self.sub(self.job.custom_password, locals()),
            )
        )

    def convert_result(self, result: Any) -> Union[str, dict]:
        try:
            if self.conversion_method == "text":
                result = str(result)
            elif self.conversion_method == "json":
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
        if self.validation_method == "text":
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

    def match_dictionary(self, result: dict, match: dict, first: bool = True) -> bool:
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

    def payload_helper(
        self,
        payload: dict,
        name: str,
        value: Optional[Any] = None,
        device: Optional[str] = None,
        section: Optional[str] = None,
        operation: str = "set",
    ) -> Any:
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
            if name not in payload:
                raise Exception(f"Payload Editor: {name} not found in {payload}.")
            return payload[name]

    def get_var(
        self, payload: dict, name: str, device: Optional[Any] = None, **kwargs: Any
    ) -> Any:
        return self.payload_helper(payload, name, device=device, **kwargs)

    def get_result(self, job: str, device: Optional[str] = None) -> dict:
        job_id = fetch("Job", name=job).id
        runs = fetch(
            "Run",
            allow_none=bool(self.restart_runtime),
            all_matches=True,
            parent_runtime=self.parent_runtime,
            job_id=job_id,
        )
        results: list = list(filter(None, [run.result(device) for run in runs]))
        if not results and self.restart_runtime:
            runs = fetch(
                "Run",
                all_matches=True,
                parent_runtime=self.restart_runtime,
                job_id=job_id,
            )
            results = list(filter(None, [run.result(device) for run in runs]))
        result = results.pop().result
        return result

    def python_code_kwargs(_self, **locals: Any) -> dict:  # noqa: N805
        return {
            "config": app.custom_config,
            "get_var": partial(_self.get_var, locals.get("payload", {})),
            "get_result": _self.get_result,
            "workflow": _self.workflow,
            "set_var": partial(_self.payload_helper, locals.get("payload", {})),
            "workflow_device": _self.workflow_device,
            **locals,
        }

    def eval(_self, query: str, **locals: Any) -> Any:  # noqa: N805
        try:
            return eval(query, _self.python_code_kwargs(**locals))
        except Exception as exc:
            raise Exception(
                "Python Query / Variable Substitution Failure."
                " Check that all variables are defined."
                " If you are using the 'device' variable, "
                f"check that the service has targets. ({str(exc)})"
            )

    def sub(self, input: Any, variables: dict) -> dict:
        r = compile("{{(.*?)}}")

        def replace(match: Match) -> str:
            return str(self.eval(match.group()[2:-2], **variables))

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

    def space_deleter(self, input: str) -> str:
        return "".join(input.split())

    @property
    def name(self) -> str:
        return repr(self)


class Job(AbstractBase):

    __tablename__ = "Job"
    type = Column(SmallString)
    __mapper_args__ = {"polymorphic_identity": "Job", "polymorphic_on": type}
    id = Column(Integer, primary_key=True)
    hidden = Column(Boolean, default=False)
    name = Column(SmallString, unique=True)
    last_modified = Column(SmallString)
    description = Column(SmallString)
    number_of_retries = Column(Integer, default=0)
    time_between_retries = Column(Integer, default=10)
    positions = Column(MutableDict)
    credentials = Column(SmallString, default="device")
    tasks = relationship("Task", back_populates="job", cascade="all,delete")
    vendor = Column(SmallString)
    operating_system = Column(SmallString)
    waiting_time = Column(Integer, default=0)
    creator = Column(SmallString, default="admin")
    push_to_git = Column(Boolean, default=False)
    workflows = relationship(
        "Workflow", secondary=job_workflow_table, back_populates="jobs"
    )
    python_query = Column(SmallString)
    query_property_type = Column(SmallString, default="ip_address")
    devices = relationship("Device", secondary=job_device_table, back_populates="jobs")
    pools = relationship("Pool", secondary=job_pool_table, back_populates="jobs")
    events = relationship("Event", secondary=job_event_table, back_populates="jobs")
    send_notification = Column(Boolean, default=False)
    send_notification_method = Column(SmallString, default="mail_feedback_notification")
    notification_header = Column(LargeString, default="")
    display_only_failed_nodes = Column(Boolean, default=True)
    include_link_in_summary = Column(Boolean, default=True)
    mail_recipient = Column(SmallString)
    shape = Column(SmallString, default="box")
    size = Column(Integer, default=40)
    color = Column(SmallString, default="#D2E5FF")
    initial_payload = Column(MutableDict)
    custom_username = Column(SmallString)
    custom_password = Column(SmallString)
    start_new_connection = Column(Boolean, default=False)
    skip = Column(Boolean, default=False)
    skip_python_query = Column(SmallString)
    iteration_values = Column(LargeString)
    iteration_variable_name = Column(SmallString, default="iteration_value")
    success_query = Column(SmallString)
    runs = relationship("Run", back_populates="job", cascade="all, delete-orphan")

    @property
    def filename(self) -> str:
        return app.strip_all(self.name)

    def adjacent_jobs(
        self, workflow: "Workflow", direction: str, subtype: str
    ) -> Generator[Tuple["Job", "WorkflowEdge"], None, None]:
        for edge in getattr(self, f"{direction}s"):
            if edge.subtype == subtype and edge.workflow == workflow:
                yield getattr(edge, direction), edge

    def git_push(self, results: dict) -> None:
        path_git_folder = Path.cwd() / "git" / "automation"
        with open(path_git_folder / self.name, "w") as file:
            file.write(app.str_dict(results))
        repo = Repo(str(path_git_folder))
        try:
            repo.git.add(A=True)
            repo.git.commit(m=f"Automatic commit ({self.name})")
        except GitCommandError:
            pass
        repo.remotes.origin.push()


class Service(Job):

    __tablename__ = "Service"
    __mapper_args__ = {"polymorphic_identity": "Service"}
    parent_cls = "Job"
    id = Column(Integer, ForeignKey("Job.id"), primary_key=True)
    multiprocessing = Column(Boolean, default=False)
    max_processes = Column(Integer, default=5)

    @staticmethod
    def get_device_result(args: tuple) -> None:
        device = fetch("Device", id=args[0])
        run = fetch("Run", runtime=args[1])
        device_result = run.get_results(args[2], device)
        with args[3]:
            args[4][device.name] = device_result

    def device_run(
        self, run: "Run", payload: dict, targets: Optional[Set["Device"]] = None
    ) -> dict:
        if not targets:
            return run.get_results(payload)
        else:
            if run.multiprocessing:
                device_results: dict = {}
                thread_lock = Lock()
                processes = min(len(targets), run.max_processes)
                process_args = [
                    (device.id, run.runtime, payload, thread_lock, device_results)
                    for device in targets
                ]
                pool = ThreadPool(processes=processes)
                pool.map(self.get_device_result, process_args)
                pool.close()
                pool.join()
            else:
                device_results = {
                    device.name: run.get_results(payload, device) for device in targets
                }
            for device_name, r in deepcopy(device_results).items():
                device = fetch("Device", name=device_name)
                run.create_result(r, device)
            results = {"devices": device_results}
            return results

    def build_results(self, run: "Run", payload: dict, *other: Any) -> dict:
        results: dict = {"results": {}, "success": False, "runtime": run.runtime}
        targets: Set = set()
        if run.has_targets:
            try:
                targets = run.compute_devices(payload)
                results["results"]["devices"] = {}
            except Exception as exc:
                return {"success": False, "error": str(exc)}
        for i in range(run.number_of_retries + 1):
            run.log("info", f"Running {self.type} {self.name} (attempt n°{i + 1})")
            run.set_state(completed=0, failed=0)
            attempt = self.device_run(run, payload, targets)
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
                    if run.number_of_retries:
                        results[f"Attempt {i + 1}"] = attempt
                    if i != run.number_of_retries:
                        sleep(run.time_between_retries)
                    else:
                        for device in targets:
                            results["results"]["devices"][device.name] = attempt[
                                "devices"
                            ][device.name]
            else:
                if run.number_of_retries:
                    results[f"Attempts {i + 1}"] = attempt
                if attempt["success"] or i == run.number_of_retries:
                    results["results"] = attempt
                    results["success"] = attempt["success"]
                    break
                else:
                    sleep(run.time_between_retries)
        return results

    def generate_row(self, table: str) -> List[str]:
        number_of_runs = app.job_db[self.id]["runs"]
        return [
            f"Running ({number_of_runs})" if number_of_runs else "Idle",
            f"""<button type="button" class="btn btn-info btn-xs"
            onclick="showLogsPanel({self.row_properties})">
            </i>Logs</a></button>""",
            f"""<button type="button" class="btn btn-info btn-xs"
            onclick="showResultsPanel('{self.id}', '{self.name}', 'service')">
            </i>Results</a></button>""",
            f"""<button type="button" class="btn btn-success btn-xs"
            onclick="normalRun('{self.id}')">Run</button>""",
            f"""<button type="button" class="btn btn-success btn-xs"
            onclick="showTypePanel('{self.type}', '{self.id}', 'run')">
            Run with Updates</button>""",
            f"""<button type="button" class="btn btn-primary btn-xs"
            onclick="showTypePanel('{self.type}', '{self.id}')">Edit</button>""",
            f"""<button type="button" class="btn btn-primary btn-xs"
            onclick="showTypePanel('{self.type}', '{self.id}', 'duplicate')">
            Duplicate</button>""",
            f"""<button type="button" class="btn btn-primary btn-xs"
            onclick="exportJob('{self.id}')">
            Export</button>""",
            f"""<button type="button" class="btn btn-danger btn-xs"
            onclick="showDeletionPanel('service', '{self.id}', '{self.name}')">
            Delete</button>""",
        ]


class Workflow(Job):

    __tablename__ = "Workflow"
    __mapper_args__ = {"polymorphic_identity": "Workflow"}
    parent_cls = "Job"
    has_targets = Column(Boolean, default=True)
    id = Column(Integer, ForeignKey("Job.id"), primary_key=True)
    labels = Column(MutableDict)
    device_targets_mode = Column(SmallString, default="service")
    jobs = relationship("Job", secondary=job_workflow_table, back_populates="workflows")
    edges = relationship(
        "WorkflowEdge", back_populates="workflow", cascade="all, delete-orphan"
    )
    start_jobs = relationship(
        "Job", secondary=start_jobs_workflow_table, backref="start_workflows"
    )

    def __init__(self, **kwargs: Any) -> None:
        start, end = fetch("Service", name="Start"), fetch("Service", name="End")
        self.jobs.extend([start, end])
        super().__init__(**kwargs)
        if not kwargs.get("start_jobs"):
            self.start_jobs = [start]
        if self.name not in end.positions:
            end.positions[self.name] = (500, 0)

    def generate_row(self, table: str) -> List[str]:
        number_of_runs = app.job_db[self.id]["runs"]
        return [
            f"Running ({number_of_runs})" if number_of_runs else "Idle",
            f"""<button type="button" class="btn btn-info btn-xs"
            onclick="showLogsPanel('{self.id}', '{self.name}', '{self.type}')">
            </i>Logs</a></button>""",
            f"""<button type="button" class="btn btn-info btn-xs"
            onclick="showResultsPanel('{self.id}', '{self.name}', 'workflow')">
            </i>Results</a></button>""",
            f"""<button type="button" class="btn btn-success btn-xs"
            onclick="normalRun('{self.id}')">Run</button>""",
            f"""<button type="button" class="btn btn-success btn-xs"
            onclick="showTypePanel('{self.type}', '{self.id}', 'run')">
            Run with Updates</button>""",
            f"""<button type="button" class="btn btn-primary btn-xs"
            onclick="showTypePanel('workflow', '{self.id}')">
            Edit</button>""",
            f"""<button type="button" class="btn btn-primary btn-xs"
            onclick="showTypePanel('workflow', '{self.id}', 'duplicate')">
            Duplicate</button>""",
            f"""<button type="button" class="btn btn-primary btn-xs"
            onclick="exportJob('{self.id}')">
            Export</button>""",
            f"""<button type="button" class="btn btn-danger btn-xs"
            onclick="showDeletionPanel('workflow', '{self.id}', '{self.name}')">
            Delete</button>""",
        ]

    def compute_valid_devices(
        self, run: Run, job: Job, allowed_devices: dict, payload: dict
    ) -> Set[Device]:
        if job.type != "Workflow" and not job.has_targets:
            return set()
        elif run.device_targets_mode == "service":
            return allowed_devices[job.name]
        else:
            return run.compute_devices(payload)

    def workflow_targets_processing(
        self, runtime: str, allowed_devices: dict, job: Job, results: dict
    ) -> Generator[Job, None, None]:
        failed_devices, passed_devices = set(), set()
        skip_job = results["success"] == "skipped"
        if (job.type == "Workflow" or job.has_targets) and not skip_job:
            if "devices" in results["results"]:
                devices = results["results"]["devices"]
            else:
                devices = results.get("devices", {})
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
        for devices, edge_type in (
            (passed_devices, "success"),
            (failed_devices, "failure"),
        ):
            if not devices:
                continue
            for successor, edge in job.adjacent_jobs(self, "destination", edge_type):
                allowed_devices[successor.name] |= devices
                app.run_db[runtime]["edges"][edge.id] = len(devices)
                yield successor

    def per_device_workflow_run(
        self, run: "Run", payload: dict, device: Device
    ) -> dict:
        app.run_db[run.runtime].update({"jobs": defaultdict(dict), "edges": {}})
        jobs: list = list(run.start_jobs)
        payload = deepcopy(payload)
        visited: Set = set()
        results: dict = {"results": {}, "success": False, "runtime": run.runtime}
        while jobs:
            job = jobs.pop()
            if job in visited:
                continue
            if any(
                node not in visited
                for node, _ in job.adjacent_jobs(self, "source", "prerequisite")
            ):
                continue
            visited.add(job)
            app.run_db[run.runtime]["current_job"] = job.get_properties()
            skip_job = False
            if job.skip_python_query:
                skip_job = run.eval(job.skip_python_query, **locals())
            if skip_job or job.skip:
                job_results = {"success": "skipped"}
            elif job.python_query:
                try:
                    job_run = factory(
                        "Run",
                        job=job.id,
                        workflow=self.id,
                        workflow_device=device.id,
                        parent_runtime=run.parent_runtime,
                        restart_runtime=run.restart_runtime,
                    )
                    job_run.properties = {}
                    result = job_run.run(payload)
                except Exception as exc:
                    result = {"success": False, "error": str(exc)}
                job_results = result
            else:
                job_run = factory(
                    "Run",
                    job=job.id,
                    workflow=self.id,
                    parent_runtime=run.parent_runtime,
                    restart_runtime=run.restart_runtime,
                )
                job_run.properties = {"devices": [device.id]}
                Session.commit()
                job_results = job_run.run(payload)
            app.run_db[run.runtime]["jobs"][job.id]["success"] = job_results[
                "success"
            ]
            successors = (
                successor
                for successor, _ in job.adjacent_jobs(
                    self,
                    "destination",
                    "success" if job_results["success"] else "failure",
                )
            )
            payload[job.name] = job_results
            results["results"].update(payload)
            for successor in successors:
                jobs.append(successor)
                if successor == self.jobs[1]:
                    results["success"] = True
            if not skip_job and not job.skip:
                sleep(job.waiting_time)
        return results

    def build_results(self, run: "Run", payload: dict) -> dict:
        if run.device_targets_mode in ("service", "ignore"):
            return self.per_service_workflow_run(run, payload)
        else:
            target_results = {
                target.name: self.per_device_workflow_run(run, payload, target)
                for target in run.compute_devices(payload)
            }
            success = all(r["success"] for r in target_results.values())
            return {
                "results": target_results,
                "success": success,
                "runtime": run.runtime,
            }

    @property
    def job_number(self) -> int:
        return sum(
            (1 + job.job_number) if job.type == "Workflow" else 1 for job in self.jobs
        )

    def per_service_workflow_run(self, run: "Run", payload: dict) -> dict:
        app.run_db[run.runtime].update(
            {"jobs": defaultdict(dict), "edges": {}, "progress": defaultdict(int)}
        )
        run.set_state(progress_max=self.job_number)
        jobs: list = list(run.start_jobs)
        payload = deepcopy(payload)
        visited: Set = set()
        results: dict = {"results": {}, "success": False, "runtime": run.runtime}
        allowed_devices: dict = defaultdict(set)
        if run.device_targets_mode == "service":
            initial_targets = set(run.compute_devices(payload))
            for job in jobs:
                allowed_devices[job.name] = initial_targets
        while jobs:
            job = jobs.pop()
            if job in visited or any(
                node not in visited
                for node, _ in job.adjacent_jobs(self, "source", "prerequisite")
            ):
                continue
            visited.add(job)
            app.run_db[run.runtime]["current_job"] = job.get_properties()
            skip_job = False
            if job.skip_python_query:
                skip_job = run.eval(job.skip_python_query, **locals())
            if skip_job or job.skip:
                job_results = {"success": "skipped"}
            elif run.device_targets_mode == "service" and job.python_query:
                device_results, success = {}, True
                for base_target in allowed_devices[job.name]:
                    try:
                        job_run = factory(
                            "Run",
                            job=job.id,
                            workflow=self.id,
                            workflow_device=base_target.id,
                            parent_runtime=run.parent_runtime,
                            restart_runtime=run.restart_runtime,
                        )
                        job_run.properties = {}
                        derived_target_result = job_run.run(payload)
                        device_results[base_target.name] = derived_target_result
                        if not derived_target_result["success"]:
                            success = False
                    except Exception as exc:
                        device_results[base_target.name] = {
                            "success": False,
                            "error": str(exc),
                        }
                job_results = {  # type: ignore
                    "results": {"devices": device_results},
                    "success": success,
                }
            else:
                valid_devices = self.compute_valid_devices(
                    run, job, allowed_devices, payload
                )
                job_run = factory(
                    "Run",
                    job=job.id,
                    workflow=self.id,
                    parent_runtime=run.parent_runtime,
                    restart_runtime=run.restart_runtime,
                )
                job_run.properties = {"devices": [d.id for d in valid_devices]}
                Session.commit()
                job_results = job_run.run(payload)
            app.run_db[run.runtime]["jobs"][job.id]["success"] = job_results["success"]
            if run.device_targets_mode == "service":
                successors = self.workflow_targets_processing(
                    run.runtime, allowed_devices, job, job_results
                )
            else:
                successors = (
                    successor
                    for successor, _ in job.adjacent_jobs(
                        self,
                        "destination",
                        "success" if job_results["success"] else "failure",
                    )
                )
            payload[job.name] = job_results
            results["results"].update(payload)
            for successor in successors:
                jobs.append(successor)
                if (
                    not run.device_targets_mode == "service"
                    and successor == self.jobs[1]
                ):
                    results["success"] = True
            if not skip_job and not job.skip:
                sleep(job.waiting_time)
        if run.device_targets_mode == "service":
            end_devices = allowed_devices["End"]
            results["devices"] = {
                device.name: {"success": device in end_devices}
                for device in initial_targets
            }
            results["success"] = initial_targets == end_devices
        return results


class WorkflowEdge(AbstractBase):

    __tablename__ = type = "WorkflowEdge"
    id = Column(Integer, primary_key=True)
    name = Column(SmallString)
    label = Column(SmallString)
    subtype = Column(SmallString)
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

    def __init__(self, *args, **kwargs):
        self.label = kwargs["subtype"]
        super().__init__(*args, **kwargs)
