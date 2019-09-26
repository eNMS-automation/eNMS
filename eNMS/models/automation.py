from copy import deepcopy
from git import Repo
from git.exc import GitCommandError
from multiprocessing import Lock
from multiprocessing.pool import ThreadPool
from pathlib import Path
from sqlalchemy import Boolean, ForeignKey, Integer
from sqlalchemy.orm import backref, relationship
from time import sleep

from eNMS import app
from eNMS.database.dialect import Column, LargeString, MutableDict, SmallString
from eNMS.database.functions import fetch
from eNMS.database.associations import (
    service_device_table,
    service_event_table,
    service_pool_table,
    service_workflow_table,
)
from eNMS.database.base import AbstractBase
from eNMS.models.inventory import Device  # noqa: F401
from eNMS.models.execution import Run  # noqa: F401
from eNMS.models.events import Task  # noqa: F401
from eNMS.models.administration import User  # noqa: F401


class Service(AbstractBase):

    __tablename__ = "service"
    type = Column(SmallString)
    __mapper_args__ = {"polymorphic_identity": "service", "polymorphic_on": type}
    id = Column(Integer, primary_key=True)
    hidden = Column(Boolean, default=False)
    name = Column(SmallString, unique=True)
    last_modified = Column(SmallString)
    description = Column(SmallString)
    number_of_retries = Column(Integer, default=0)
    time_between_retries = Column(Integer, default=10)
    positions = Column(MutableDict)
    credentials = Column(SmallString, default="device")
    tasks = relationship("Task", back_populates="service", cascade="all,delete")
    vendor = Column(SmallString)
    operating_system = Column(SmallString)
    waiting_time = Column(Integer, default=0)
    creator = Column(SmallString, default="admin")
    push_to_git = Column(Boolean, default=False)
    workflows = relationship(
        "Workflow", secondary=service_workflow_table, back_populates="services"
    )
    python_query = Column(SmallString)
    query_property_type = Column(SmallString, default="ip_address")
    devices = relationship("Device", secondary=service_device_table, back_populates="services")
    pools = relationship("Pool", secondary=service_pool_table, back_populates="services")
    events = relationship("Event", secondary=service_event_table, back_populates="services")
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
    runs = relationship("Run", back_populates="service", cascade="all, delete-orphan")
    maximum_runs = Column(Integer, default=1)
    multiprocessing = Column(Boolean, default=False)
    max_processes = Column(Integer, default=5)

    @property
    def filename(self):
        return app.strip_all(self.name)

    def generate_row(self, table):
        number_of_runs = app.service_db[self.id]["runs"]
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
              <li><a href="#" onclick="exportService('{self.id}')">Export</a></li>
            </ul>
            </div>""",
            f"""<button type="button" class="btn btn-danger btn-sm"
            onclick="showDeletionPanel({self.row_properties})">
            Delete</button>""",
        ]

    def adjacent_services(self, workflow, direction, subtype):
        for edge in getattr(self, f"{direction}s"):
            if edge.subtype == subtype and edge.workflow == workflow:
                yield getattr(edge, direction), edge

    def git_push(self, results):
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

    @staticmethod
    def get_device_result(args):
        device = fetch("device", id=args[0])
        run = fetch("run", runtime=args[1])
        device_result = run.get_results(args[2], device)
        with args[3]:
            args[4][device.name] = device_result

    def device_run(self, run, payload, targets=None):
        if not targets:
            return run.get_results(payload)
        else:
            if run.multiprocessing:
                device_results = {}
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

    def build_results(self, run, payload, *other):
        results = {"results": {}, "success": False, "runtime": run.runtime}
        targets = set()
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


class WorkflowEdge(AbstractBase):

    __tablename__ = type = "workflow_edge"
    id = Column(Integer, primary_key=True)
    name = Column(SmallString)
    label = Column(SmallString)
    subtype = Column(SmallString)
    source_id = Column(Integer, ForeignKey("service.id"))
    source = relationship(
        "Service",
        primaryjoin="Service.id == WorkflowEdge.source_id",
        backref=backref("destinations", cascade="all, delete-orphan"),
        foreign_keys="WorkflowEdge.source_id",
    )
    destination_id = Column(Integer, ForeignKey("service.id"))
    destination = relationship(
        "Service",
        primaryjoin="Service.id == WorkflowEdge.destination_id",
        backref=backref("sources", cascade="all, delete-orphan"),
        foreign_keys="WorkflowEdge.destination_id",
    )
    workflow_id = Column(Integer, ForeignKey("workflow.id"))
    workflow = relationship(
        "Workflow", back_populates="edges", foreign_keys="WorkflowEdge.workflow_id"
    )

    def __init__(self, **kwargs):
        self.label = kwargs["subtype"]
        super().__init__(**kwargs)
