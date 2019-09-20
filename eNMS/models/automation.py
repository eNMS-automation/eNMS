from collections import defaultdict
from copy import deepcopy
from git import Repo
from git.exc import GitCommandError
from multiprocessing import Lock
from multiprocessing.pool import ThreadPool
from pathlib import Path
from sqlalchemy import Boolean, ForeignKey, Integer
from sqlalchemy.orm import backref, relationship
from time import sleep
from typing import Any, Generator, List, Optional, Set, Tuple

from eNMS import app
from eNMS.database import Session
from eNMS.database.dialect import Column, LargeString, MutableDict, SmallString
from eNMS.database.functions import factory, fetch
from eNMS.database.associations import (
    job_device_table,
    job_event_table,
    job_pool_table,
    job_workflow_table,
    start_jobs_workflow_table,
)
from eNMS.database.base import AbstractBase
from eNMS.models.inventory import Device
from eNMS.models.execution import Run
from eNMS.models.events import Task  # noqa: F401
from eNMS.models.administration import User  # noqa: F401


class Job(AbstractBase):

    __tablename__ = "job"
    type = Column(SmallString)
    __mapper_args__ = {"polymorphic_identity": "job", "polymorphic_on": type}
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
    color = Column(SmallString, default="#D2E5FF")
    initial_payload = Column(MutableDict)
    custom_username = Column(SmallString)
    custom_password = Column(SmallString)
    start_new_connection = Column(Boolean, default=False)
    skip = Column(Boolean, default=False)
    skip_python_query = Column(SmallString)
    iteration_values = Column(LargeString)
    iteration_variable_name = Column(SmallString, default="iteration_value")
    result_postprocessing = Column(LargeString)
    runs = relationship("Run", back_populates="job", cascade="all, delete-orphan")
    maximum_runs = Column(Integer, default=1)

    @property
    def filename(self) -> str:
        return app.strip_all(self.name)

    def generate_row(self, table: str) -> List[str]:
        number_of_runs = app.job_db[self.id]["runs"]
        return [
            f"Running ({number_of_runs})" if number_of_runs else "Idle",
            f"""<div class="btn-group" style="width: 100px;">
            <button type="button" class="btn btn-info btn-sm"
            onclick="showResultsPanel({self.row_properties})">
            </i>Results</a></button>,
            <button type="button" class="btn btn-info btn-sm
            dropdown-toggle" data-toggle="dropdown">
              <span class="caret"></span>
            </button>
            <ul class="dropdown-menu" role="menu">
              <li><a href="#" onclick="showLogsPanel({self.row_properties})">
              Logs</a></li>
            </ul>
            </div>""",
            f"""<div class="btn-group" style="width: 80px;">
            <button type="button" class="btn btn-success btn-sm"
            onclick="normalRun('{self.id}')">Run</button>,
            <button type="button" class="btn btn-success btn-sm
            dropdown-toggle" data-toggle="dropdown">
              <span class="caret"></span>
            </button>
            <ul class="dropdown-menu" role="menu">
              <li><a href="#" onclick="showTypePanel('{self.type}', '{self.id}',
              'run')">Run with Updates</a></li>
            </ul>
            </div>""",
            f"""<div class="btn-group" style="width: 80px;">
            <button type="button" class="btn btn-primary btn-sm"
            onclick="showTypePanel('{self.type}', '{self.id}')">Edit</button>,
            <button type="button" class="btn btn-primary btn-sm
            dropdown-toggle" data-toggle="dropdown">
              <span class="caret"></span>
            </button>
            <ul class="dropdown-menu" role="menu">
              <li><a href="#" onclick="showTypePanel('{self.type}', '{self.id}',
              'duplicate')">Duplicate</a></li>
              <li><a href="#" onclick="exportJob('{self.id}')">Export</a></li>
            </ul>
            </div>""",
            f"""<button type="button" class="btn btn-danger btn-sm"
            onclick="showDeletionPanel({self.row_properties})">
            Delete</button>""",
        ]

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

    __tablename__ = "service"
    __mapper_args__ = {"polymorphic_identity": "service"}
    parent_type = "job"
    id = Column(Integer, ForeignKey("job.id"), primary_key=True)
    multiprocessing = Column(Boolean, default=False)
    max_processes = Column(Integer, default=5)

    @staticmethod
    def get_device_result(args: tuple) -> None:
        device = fetch("device", id=args[0])
        run = fetch("run", runtime=args[1])
        device_result = run.get_results(args[2], device)
        with args[3]:
            args[4][device.name] = device_result

    def device_run(
        self, run: Run, payload: dict, targets: Optional[Set["Device"]] = None
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
                device = fetch("device", name=device_name)
                run.create_result(r, device)
            results = {"devices": device_results}
            return results

    def build_results(self, run: Run, payload: dict, *other: Any) -> dict:
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


class Workflow(Job):

    __tablename__ = "workflow"
    __mapper_args__ = {"polymorphic_identity": "workflow"}
    parent_type = "job"
    has_targets = Column(Boolean, default=True)
    id = Column(Integer, ForeignKey("job.id"), primary_key=True)
    labels = Column(MutableDict)
    use_workflow_devices = Column(Boolean, default=True)
    traversal_mode = Column(SmallString, default="service")
    jobs = relationship("Job", secondary=job_workflow_table, back_populates="workflows")
    edges = relationship(
        "WorkflowEdge", back_populates="workflow", cascade="all, delete-orphan"
    )
    start_jobs = relationship(
        "Job", secondary=start_jobs_workflow_table, backref="start_workflows"
    )

    def __init__(self, **kwargs: Any) -> None:
        start, end = fetch("service", name="Start"), fetch("service", name="End")
        self.jobs.extend([start, end])
        super().__init__(**kwargs)
        if not kwargs.get("start_jobs"):
            self.start_jobs = [start]
        if self.name not in end.positions:
            end.positions[self.name] = (500, 0)

    def compute_valid_devices(
        self, run: Run, job: Job, allowed_devices: dict, payload: dict
    ) -> Set[Device]:
        if job.type != "workflow" and not job.has_targets:
            return set()
        elif run.use_workflow_devices:
            return allowed_devices[job.name]
        else:
            return run.compute_devices(payload)

    def workflow_targets_processing(
        self, runtime: str, allowed_devices: dict, job: Job, results: dict
    ) -> Generator[Job, None, None]:
        failed_devices, passed_devices = set(), set()
        skip_job = results["success"] == "skipped"
        if (job.type == "workflow" or job.has_targets) and not skip_job:
            if "devices" in results["results"]:
                devices = results["results"]["devices"]
            else:
                devices = results.get("devices", {})
            for name, device_results in devices.items():
                if device_results["success"]:
                    passed_devices.add(fetch("device", name=name))
                else:
                    failed_devices.add(fetch("device", name=name))
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

    def workflow_run(
        self, run: Run, payload: dict, device: Optional[Device] = None
    ) -> dict:
        app.run_db[run.runtime].update(
            {"jobs": defaultdict(dict), "edges": {}, "progress": defaultdict(int)}
        )
        run.set_state(progress_max=self.job_number)
        number_of_runs: dict = defaultdict(int)
        jobs: list = list(run.start_jobs)
        payload = deepcopy(payload)
        visited: Set = set()
        results: dict = {"results": {}, "success": False, "runtime": run.runtime}
        allowed_devices: dict = defaultdict(set)
        if run.use_workflow_devices and run.traversal_mode == "service":
            initial_targets = set(run.compute_devices(payload))
            for job in jobs:
                allowed_devices[job.name] = initial_targets
        while jobs:
            if run.stop:
                return results
            job = jobs.pop()
            if number_of_runs[job.name] >= job.maximum_runs or any(
                node not in visited
                for node, _ in job.adjacent_jobs(self, "source", "prerequisite")
            ):
                continue
            number_of_runs[job.name] += 1
            visited.add(job)
            app.run_db[run.runtime]["current_job"] = job.get_properties()
            skip_job = False
            if job.skip_python_query:
                skip_job = run.eval(job.skip_python_query, **locals())
            if skip_job or job.skip:
                job_results = {"success": "skipped"}
            elif run.use_workflow_devices and job.python_query:
                if run.traversal_mode == "service":
                    device_results, success = {}, True
                    for base_target in allowed_devices[job.name]:
                        try:
                            job_run = factory(
                                "run",
                                job=job.id,
                                workflow=self.id,
                                workflow_device=base_target.id,
                                parent_runtime=run.parent_runtime,
                                restart_run=run.restart_run,
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
                    try:
                        job_run = factory(
                            "run",
                            job=job.id,
                            workflow=self.id,
                            workflow_device=device.id,  # type: ignore
                            parent_runtime=run.parent_runtime,
                            restart_run=run.restart_run,
                        )
                        job_run.properties = {}
                        result = job_run.run(payload)
                    except Exception as exc:
                        result = {"success": False, "error": str(exc)}
                    job_results = result
            else:
                if run.traversal_mode == "service":
                    valid_devices = self.compute_valid_devices(
                        run, job, allowed_devices, payload
                    )
                else:
                    valid_devices = {device}  # type: ignore
                job_run = factory(
                    "run",
                    job=job.id,
                    workflow=self.id,
                    parent_runtime=run.parent_runtime,
                    restart_run=run.restart_run,
                )
                job_run.properties = {"devices": [d.id for d in valid_devices]}
                Session.commit()
                job_results = job_run.run(payload)
            app.run_db[run.runtime]["jobs"][job.id]["success"] = job_results["success"]
            if run.use_workflow_devices and run.traversal_mode == "service":
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
                if (device or not run.use_workflow_devices) and successor == self.jobs[
                    1
                ]:
                    results["success"] = True
            if not skip_job and not job.skip:
                sleep(job.waiting_time)
        if run.use_workflow_devices and run.traversal_mode == "service":
            end_devices = allowed_devices["End"]
            results["devices"] = {
                device.name: {"success": device in end_devices}
                for device in initial_targets
            }
            results["success"] = initial_targets == end_devices
        return results

    def build_results(self, run: Run, payload: dict) -> dict:
        if run.traversal_mode == "service":
            return self.workflow_run(run, payload)
        else:
            device_results = {}
            for device in run.compute_devices(payload):
                if run.iteration_values:
                    targets_results = {}
                    for target in run.eval(run.iteration_values, **locals()):
                        run.payload_helper(payload, run.iteration_variable_name, target)
                        targets_results[target] = self.workflow_run(
                            run, payload, device
                        )
                    device_results[device.name] = {
                        "results": targets_results,
                        "success": all(r["success"] for r in targets_results.values()),
                    }
                else:
                    device_results[device.name] = self.workflow_run(
                        run, payload, device
                    )
            success = all(r["success"] for r in device_results.values())
            return {
                "results": {"devices": device_results},
                "success": success,
                "runtime": run.runtime,
            }

    @property
    def job_number(self) -> int:
        return sum(
            (1 + job.job_number) if job.type == "workflow" else 1 for job in self.jobs
        )


class WorkflowEdge(AbstractBase):

    __tablename__ = type = "workflow_edge"
    id = Column(Integer, primary_key=True)
    name = Column(SmallString)
    label = Column(SmallString)
    subtype = Column(SmallString)
    source_id = Column(Integer, ForeignKey("job.id"))
    source = relationship(
        "Job",
        primaryjoin="Job.id == WorkflowEdge.source_id",
        backref=backref("destinations", cascade="all, delete-orphan"),
        foreign_keys="WorkflowEdge.source_id",
    )
    destination_id = Column(Integer, ForeignKey("job.id"))
    destination = relationship(
        "Job",
        primaryjoin="Job.id == WorkflowEdge.destination_id",
        backref=backref("sources", cascade="all, delete-orphan"),
        foreign_keys="WorkflowEdge.destination_id",
    )
    workflow_id = Column(Integer, ForeignKey("workflow.id"))
    workflow = relationship(
        "Workflow", back_populates="edges", foreign_keys="WorkflowEdge.workflow_id"
    )

    def __init__(self, **kwargs: Any) -> None:
        self.label = kwargs["subtype"]
        super().__init__(**kwargs)
