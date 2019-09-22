from apscheduler.jobstores.base import JobLookupError
from collections import defaultdict
from datetime import datetime
from flask import request, session
from flask_login import current_user
from napalm._SUPPORTED_DRIVERS import SUPPORTED_DRIVERS
from netmiko.ssh_dispatcher import CLASS_MAPPER, FILE_TRANSFER_MAP
from pathlib import Path
from re import search, sub
from typing import Any, Dict, Optional
from uuid import uuid4

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
    job_db: dict = defaultdict(lambda: {"runs": 0})
    run_db: dict = defaultdict(dict)
    run_logs: dict = defaultdict(list)

    def stop_workflow(self, runtime: str) -> Optional[bool]:
        if runtime in self.run_db:
            self.run_db[runtime]["stop"] = True
            return True
        else:
            return None

    def add_edge(
        self, workflow_id: int, subtype: str, source: int, destination: int
    ) -> dict:
        workflow_edge = factory(
            "workflow_edge",
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
        fetch("workflow", id=workflow_id).last_modified = now
        return {"edge": workflow_edge.serialized, "update_time": now}

    def add_jobs_to_workflow(self, workflow_id: int, job_ids: str) -> Dict[str, Any]:
        workflow = fetch("workflow", id=workflow_id)
        jobs = objectify("job", [int(job_id) for job_id in job_ids.split("-")])
        for job in jobs:
            job.workflows.append(workflow)
        now = self.get_time()
        workflow.last_modified = now
        return {"jobs": [job.serialized for job in jobs], "update_time": now}

    def clear_results(self, job_id: int) -> None:
        for result in fetch("run", all_matches=True, allow_none=True, job_id=job_id):
            Session.delete(result)

    def create_label(self, workflow_id: int, x: int, y: int, **kwargs: Any) -> dict:
        workflow, label_id = fetch("workflow", id=workflow_id), str(uuid4())
        label = {"positions": [x, y], "content": kwargs["content"]}
        workflow.labels[label_id] = label
        return {"id": label_id, **label}

    def delete_edge(self, workflow_id: int, edge_id: int) -> str:
        delete("workflow_edge", id=edge_id)
        now = self.get_time()
        fetch("workflow", id=workflow_id).last_modified = now
        return now

    def delete_node(self, workflow_id: int, job_id: int) -> dict:
        workflow, job = fetch("workflow", id=workflow_id), fetch("job", id=job_id)
        workflow.jobs.remove(job)
        now = self.get_time()
        workflow.last_modified = now
        return {"job": job.serialized, "update_time": now}

    def delete_label(self, workflow_id: int, label: int) -> str:
        workflow = fetch("workflow", id=workflow_id)
        workflow.labels.pop(label)
        now = self.get_time()
        workflow.last_modified = now
        return now

    def duplicate_workflow(self, workflow_id: int, **kwargs: Any) -> dict:
        parent_workflow = fetch("workflow", id=workflow_id)
        new_workflow = factory("workflow", **kwargs)
        Session.commit()
        for job in parent_workflow.jobs:
            new_workflow.jobs.append(job)
            job.positions[new_workflow.name] = job.positions[parent_workflow.name]
        Session.commit()
        for edge in parent_workflow.edges:
            subtype, src, destination = edge.subtype, edge.source, edge.destination
            new_workflow.edges.append(
                factory(
                    "workflow_edge",
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

    def get_job_logs(self, **kwargs: Any) -> dict:
        run = fetch("run", allow_none=True, runtime=kwargs["runtime"])
        result = run.result() if run else None
        logs = result["logs"] if result else self.run_logs.get(kwargs["runtime"], [])
        filtered_logs = (log for log in logs if kwargs["filter"] in log)
        return {"logs": "\n".join(filtered_logs), "refresh": not bool(result)}

    def get_runtimes(self, type: str, id: int) -> list:
        if type == "device":
            results = fetch("result", allow_none=True, all_matches=True, device_id=id)
            runs = [result.run for result in results]
        else:
            runs = fetch("run", allow_none=True, all_matches=True, job_id=id)
        return sorted(set((run.runtime, run.name) for run in runs))

    def get_result(self, id: int) -> Optional[dict]:
        return fetch("result", id=id).result

    @staticmethod
    def run(job: int, **kwargs: Any) -> dict:
        run_kwargs = {
            key: kwargs.pop(key)
            for key in ("creator", "runtime", "task")
            if kwargs.get(key)
        }
        restart_run = fetch(
            "run", allow_none=True, job_id=job, runtime=kwargs.get("restart_runtime")
        )
        if restart_run:
            run_kwargs["restart_run"] = restart_run
        run = factory("run", job=job, **run_kwargs)
        run.properties = kwargs
        return run.run(kwargs.get("payload"))

    def run_job(self, id: Optional[int] = None, **kwargs: Any) -> dict:
        for property in ("user", "csrf_token", "form_type"):
            kwargs.pop(property, None)
        kwargs["creator"] = getattr(current_user, "name", "admin")
        job = fetch("job", id=id)
        kwargs["runtime"] = runtime = self.get_time()
        if kwargs.get("asynchronous", True):
            self.scheduler.add_job(
                id=self.get_time(),
                func=self.run,
                run_date=datetime.now(),
                args=[id],
                kwargs=kwargs,
                trigger="date",
            )
        else:
            job.run(runtime=runtime)
        return {**job.serialized, "runtime": runtime}

    def save_positions(self, workflow_id: int) -> str:
        now = self.get_time()
        workflow = fetch("workflow", allow_none=True, id=workflow_id)
        session["workflow"] = workflow.id
        for id, position in request.json.items():
            new_position = [position["x"], position["y"]]
            if "-" in id:
                old_position = workflow.labels[id]["positions"]
                workflow.labels[id] = {
                    "positions": new_position,
                    "content": workflow.labels[id]["content"],
                }
            else:
                job = fetch("job", id=id)
                old_position = job.positions.get(workflow.name)
                job.positions[workflow.name] = new_position
            if new_position != old_position:
                workflow.last_modified = now
        return now

    def skip_jobs(self, skip: str, job_ids: str) -> None:
        for job_id in job_ids.split("-"):
            fetch("Job", id=job_id).skip = skip == "skip"

    def get_workflow_state(
        self, workflow_id: int, runtime: Optional[str] = None
    ) -> dict:
        workflow = fetch("workflow", id=workflow_id)
        runtimes = [
            (r.runtime, r.creator)
            for r in fetch("run", allow_none=True, all_matches=True, job_id=workflow_id)
        ]
        state = None
        if runtimes and runtime not in ("normal", None):
            if runtime == "latest":
                runtime = runtimes[-1][0]
            state = self.run_db.get(runtime)
            if not state:
                results = fetch("run", runtime=runtime).results
                global_result = [r for r in results if not r.device_id]
                state = global_result[0].result.get("state") if global_result else None
        return {
            "workflow": workflow.to_dict(include=["jobs", "edges"]),
            "runtimes": runtimes,
            "state": state,
            "runtime": runtime,
        }

    def convert_date(self, date: str) -> list:
        python_month = search(r".*-(\d{2})-.*", date).group(1)  # type: ignore
        month = "{:02}".format((int(python_month) - 1) % 12)
        return [
            int(i)
            for i in sub(
                r"(\d+)-(\d+)-(\d+) (\d+):(\d+).*", r"\1," + month + r",\3,\4,\5", date
            ).split(",")
        ]

    def calendar_init(self, type: str) -> dict:
        results = {}
        for instance in fetch_all(type):
            if getattr(instance, "workflow", None):
                continue
            date = getattr(instance, "next_run_time" if type == "task" else "runtime")
            if date:
                results[instance.name] = {
                    "start": self.convert_date(date),
                    **instance.serialized,
                }
        return results

    def scheduler_action(self, action: str) -> None:
        getattr(self.scheduler, action)()

    def task_action(self, action: str, task_id: int) -> Optional[dict]:
        try:
            return getattr(fetch("task", id=task_id), action)()
        except JobLookupError:
            return {"error": "This task no longer exists."}

    def scan_playbook_folder(self) -> list:
        path = Path(self.playbook_path or self.path / "playbooks")
        playbooks = [[str(f) for f in path.glob(e)] for e in ("*.yaml", "*.yml")]
        return sorted(sum(playbooks, []))
