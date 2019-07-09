from collections import defaultdict
from datetime import datetime
from difflib import SequenceMatcher
from flask import request, session
from napalm._SUPPORTED_DRIVERS import SUPPORTED_DRIVERS
from netmiko.ssh_dispatcher import CLASS_MAPPER, FILE_TRANSFER_MAP
from pathlib import Path
from re import search, sub
from subprocess import PIPE, Popen
from typing import Any, Dict, List

from eNMS.concurrency import threaded_job
from eNMS.controller.base import BaseController
from eNMS.database import Session
from eNMS.database.functions import delete, factory, fetch, fetch_all, objectify


class AutomationController(BaseController):

    NETMIKO_DRIVERS = sorted((driver, driver) for driver in CLASS_MAPPER)
    NETMIKO_SCP_DRIVERS = sorted((driver, driver) for driver in FILE_TRANSFER_MAP)
    NAPALM_DRIVERS = sorted((driver, driver) for driver in SUPPORTED_DRIVERS[1:])
    connections_cache: dict = {
        "napalm": defaultdict(dict),
        "netmiko": defaultdict(dict),
    }

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
        for result in fetch("Result", all_matches=True, allow_none=True, job_id=job_id):
            Session.delete(result)

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

    def get_job_logs(self, name) -> dict:
        path = self.path / "logs" / "job_logs" / f"{self.strip_all(name)}.log"
        proc = Popen(['tail', '-n', "1000", path], stdout=PIPE)
        return proc.stdout.readlines()

    def get_job_timestamps(self, id: int) -> dict:
        results = fetch("Result", job_id=id, allow_none=True, all_matches=True)
        return sorted(set(result.timestamp for result in results))

    def get_results_device_list(self, id: int, **kw) -> dict:
        defaults = [("global", "Global Result"), ("all", "All devices")]
        timestamp_key = "parent_timestamp" if "job" in kw else "timestamp"
        request = {timestamp_key: kw.get("timestamp")}
        print(kw.get("job"))
        if kw.get("job") not in ("global", "all"):
            request["job_id"] = kw.get("job", id)
        print(request)
        return defaults + list(set(
            (result.device_id, result.device_name)
            for result in fetch("Result", allow_none=True, all_matches=True, **request)
            if result.device_id
        ))

    def get_workflow_results_list(self, id: int, **kw) -> dict:
        defaults = [("global", "Global Result"), ("all", "All jobs")]
        return defaults + list(set(
            (result.job_id, result.job_name)
            for result in fetch(
                "Result",
                workflow_id=id,
                parent_timestamp=kw.get("timestamp"),
                allow_none=True,
                all_matches=True,
            )
            if result.job_id
        ))

    def get_job_results(self, id: int, **kw) -> dict:
        if "timestamp" not in kw:
            return None
        service_result_window = "job" not in kw
        job, device = kw.get("job"), kw["device"]

        if service_result_window:
            timestamp = "timestamp"
        elif job == "global" and device == "global":
            timestamp = "timestamp"
        else:
            timestamp = "parent_timestamp"
        request = {timestamp: kw["timestamp"]}
        if job not in ("global", "all"):
            request["job_id"] = job
        else:
            request["job_id"] = id
        if device == "all" or job == "all":
            request["all_matches"] = True
        elif device not in ("global", "all"):
            request["device_id"] = device
        print(request)
        results = fetch("Result", allow_none=True, **request)
        if not results:
            return None
        if device == "all":
            return {
                result.device_name: result.result
                for result in results
                if result.device_id
            }
        elif job == "all":
            return {
                result.job_name: result.result
                for result in results
                if result.job_id
            }
        else:
            return results.result

    def reset_status(self) -> None:
        for job in fetch_all("Job"):
            job.is_running = False

    def restart_workflow(self, workflow_id: int, job_id: int, version: str) -> dict:
        workflow = fetch("Workflow", id=workflow_id)
        payload = workflow.results[version]["results"] if version != "null" else {}
        if workflow.is_running:
            return {"error": "Workflow is already running."}
        self.scheduler.add_job(
            id=self.get_time(),
            func=threaded_job,
            run_date=datetime.now(),
            args=[workflow_id, None, None, payload, job_id],
            trigger="date",
        )
        return workflow.name

    def run_job(self, job_id: int, asynchronous: bool = True) -> dict:
        job = fetch("Job", id=job_id)
        if job.is_running:
            return {"error": f"{job.type} is already running."}
        if asynchronous:
            self.scheduler.add_job(
                id=self.get_time(),
                func=threaded_job,
                run_date=datetime.now(),
                args=[job.id],
                trigger="date",
            )
        else:
            job.run()
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

    def scan_playbook_folder(self) -> list:
        path = Path(self.playbook_path or self.path / "playbooks")
        playbooks = [[str(f) for f in path.glob(e)] for e in ("*.yaml", "*.yml")]
        return sum(playbooks, [])
