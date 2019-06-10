from datetime import datetime
from difflib import SequenceMatcher
from flask import request, session
from napalm._SUPPORTED_DRIVERS import SUPPORTED_DRIVERS
from netmiko.ssh_dispatcher import CLASS_MAPPER, FILE_TRANSFER_MAP
from re import search, sub
from typing import Any, Dict, List

from eNMS.concurrent import threaded_job
from eNMS.controller.base import BaseController
from eNMS.database import Session
from eNMS.database.functions import delete, factory, fetch, fetch_all, objectify


class AutomationController(BaseController):

    NETMIKO_DRIVERS = sorted((driver, driver) for driver in CLASS_MAPPER)
    NETMIKO_SCP_DRIVERS = sorted((driver, driver) for driver in FILE_TRANSFER_MAP)
    NAPALM_DRIVERS = sorted((driver, driver) for driver in SUPPORTED_DRIVERS[1:])

    def add_edge(
        self, workflow_id: int, subtype: str, source: int, destination: int
    ) -> dict:
        workflow_edge = factory(
            "WorkflowEdge",
            **{
                "name": f"{workflow_id}-{subtype}:{source}->{destination}",
                "workflow": workflow_id,
                "subtype": subtype,
                "source": source,
                "destination": destination,
            },
        )
        Session.commit()
        now = self.get_time()
        fetch("Workflow", id=workflow_id).last_modified = now
        return {"edge": workflow_edge.serialized, "update_time": now}

    def add_jobs_to_workflow(self, workflow_id: int, job_ids: str) -> Dict[str, Any]:
        workflow = fetch("Workflow", id=workflow_id)
        jobs = objectify("Job", [int(job_id) for job_id in job_ids.split("-")])
        for job in jobs:
            job.workflows.append(workflow)
        now = self.get_time()
        workflow.last_modified = now
        return {"jobs": [job.serialized for job in jobs], "update_time": now}

    def clear_results(self, job_id: int) -> None:
        fetch("Job", id=job_id).results = {}

    def delete_edge(self, workflow_id: int, edge_id: int) -> str:
        delete("WorkflowEdge", id=edge_id)
        now = self.get_time()
        fetch("Workflow", id=workflow_id).last_modified = now
        return now

    def delete_node(self, workflow_id: int, job_id: int) -> dict:
        workflow, job = fetch("Workflow", id=workflow_id), fetch("Job", id=job_id)
        workflow.jobs.remove(job)
        now = self.get_time()
        workflow.last_modified = now
        return {"job": job.serialized, "update_time": now}

    def duplicate_workflow(self, workflow_id: int, **kwargs: Any) -> dict:
        parent_workflow = fetch("Workflow", id=workflow_id)
        new_workflow = factory("Workflow", **kwargs)
        Session.commit()
        for job in parent_workflow.jobs:
            new_workflow.jobs.append(job)
            job.positions[new_workflow.name] = job.positions[parent_workflow.name]
        Session.commit()
        for edge in parent_workflow.edges:
            subtype, src, destination = edge.subtype, edge.source, edge.destination
            new_workflow.edges.append(
                factory(
                    "WorkflowEdge",
                    **{
                        "name": (
                            f"{new_workflow.id}-{subtype}:"
                            f"{src.id}->{destination.id}"
                        ),
                        "workflow": new_workflow.id,
                        "subtype": subtype,
                        "source": src.id,
                        "destination": destination.id,
                    },
                )
            )
        return new_workflow.serialized

    def get_job_logs(self, id: int) -> dict:
        job = fetch("Job", id=id)
        return {"logs": job.logs, "running": job.is_running}

    def get_job_results(self, id: int) -> dict:
        return fetch("Job", id=id).results

    def reset_status(self) -> None:
        for job in fetch_all("Job"):
            job.is_running = False

    def run_job(self, job_id: int) -> dict:
        job = fetch("Job", id=job_id)
        if job.is_running:
            return {"error": "Job is already running."}
        targets = job.compute_targets()
        if hasattr(job, "has_targets"):
            if job.has_targets and not targets:
                return {"error": "Set devices or pools as targets first."}
            if not job.has_targets and targets:
                return {"error": "This service should not have targets configured."}
        self.scheduler.add_job(
            id=self.get_time(),
            func=threaded_job,
            run_date=datetime.now(),
            args=[job.id],
            trigger="date",
        )
        return job.serialized

    def save_device_jobs(self, device_id: int, **kwargs: List[int]) -> None:
        fetch("Device", id=device_id).jobs = objectify("Job", kwargs["jobs"])

    def save_positions(self, workflow_id: int) -> str:
        now = self.get_time()
        workflow = fetch("Workflow", allow_none=True, id=workflow_id)
        workflow.last_modified = now
        session["workflow"] = workflow.id
        for job_id, position in request.json.items():
            job = fetch("Job", id=job_id)
            job.positions[workflow.name] = (position["x"], position["y"])
        return now

    def get_results_diff(self, job_id: int, v1: str, v2: str) -> dict:
        job = fetch("Job", id=job_id)
        first = self.str_dict(
            dict(reversed(sorted(job.results[v1].items())))
        ).splitlines()
        second = self.str_dict(
            dict(reversed(sorted(job.results[v2].items())))
        ).splitlines()
        opcodes = SequenceMatcher(None, first, second).get_opcodes()
        return {"first": first, "second": second, "opcodes": opcodes}

    def calendar_init(self) -> dict:
        tasks = {}
        for task in fetch_all("Task"):
            # javascript dates range from 0 to 11, we must account for that by
            # substracting 1 to the month for the date to be properly displayed in
            # the calendar
            date = task.next_run_time
            if not date:
                continue
            python_month = search(r".*-(\d{2})-.*", date).group(1)  # type: ignore
            month = "{:02}".format((int(python_month) - 1) % 12)
            js_date = [
                int(i)
                for i in sub(
                    r"(\d+)-(\d+)-(\d+) (\d+):(\d+).*",
                    r"\1," + month + r",\3,\4,\5",
                    date,
                ).split(",")
            ]
            tasks[task.name] = {**task.serialized, **{"date": js_date}}
        return tasks

    def scheduler_action(self, action: str) -> None:
        getattr(self.scheduler, action)()

    def task_action(self, action: str, task_id: int) -> None:
        getattr(fetch("Task", id=task_id), action)()
