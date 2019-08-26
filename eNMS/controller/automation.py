from apscheduler.jobstores.base import JobLookupError
from collections import defaultdict
from datetime import datetime
from difflib import SequenceMatcher
from flask import request, session
from flask_login import current_user
from napalm._SUPPORTED_DRIVERS import SUPPORTED_DRIVERS
from netmiko.ssh_dispatcher import CLASS_MAPPER, FILE_TRANSFER_MAP
from operator import attrgetter
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
        for result in fetch("Run", all_matches=True, allow_none=True, job_id=job_id):
            Session.delete(result)

    def create_label(self, workflow_id: int, x: int, y: int, **kwargs: Any) -> dict:
        workflow, label_id = fetch("Workflow", id=workflow_id), str(uuid4())
        label = {"positions": [x, y], "content": kwargs["content"]}
        workflow.labels[label_id] = label
        return {"id": label_id, **label}

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

    def delete_label(self, workflow_id: int, label: int) -> str:
        workflow = fetch("Workflow", id=workflow_id)
        workflow.labels.pop(label)
        now = self.get_time()
        workflow.last_modified = now
        return now

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

    def get_job_logs(self, **kwargs: Any) -> dict:
        run = fetch("Run", allow_none=True, runtime=kwargs["runtime"])
        result = run.result() if run else None
        logs = result["logs"] if result else self.run_logs.get(kwargs["runtime"], [])
        filtered_logs = (log for log in logs if kwargs["filter"] in log)
        return {"logs": "\n".join(filtered_logs), "refresh": not bool(result)}

    def get_runtimes(self, type: str, id: int) -> list:
        if type == "device":
            results = fetch("Result", allow_none=True, all_matches=True, device_id=id)
            runs = [result.run for result in results]
        else:
            runs = fetch("Run", allow_none=True, all_matches=True, job_id=id)
        return sorted(set((run.runtime, run.name) for run in runs))

    def get_workflow_device_list(self, id: int, **kw: Any) -> dict:
        comp = "_compare" if kw["compare"] else ""
        if kw.get(f"job{comp}") in ("global", "all"):
            workflow_devices: list = []
        else:
            runtime_key = "parent_runtime" if "job" in kw else "runtime"
            request = {runtime_key: kw.get(f"runtime{comp}")}
            request["job_id"] = kw.get(f"job{comp}")
            runs = fetch("Run", allow_none=True, all_matches=True, **request)
            workflow_devices = [
                (r.workflow_device_id, r.workflow_device.name)
                for r in runs
                if r.workflow_device_id
            ]
        return {
            "workflow_devices": workflow_devices,
            "devices": self.get_device_list(id, **kw),
        }

    def get_device_list(self, id: int, **kw: Any) -> list:
        comp = "_compare" if kw["compare"] else ""
        defaults = [
            ("global", "Entire job payload"),
            ("all", "All devices"),
            ("all failed", "All devices that failed"),
            ("all passed", "All devices that passed"),
        ]
        if "runtime" not in kw:
            request: Any = {"id": id}
        else:
            runtime_key = "parent_runtime" if "job" in kw else "runtime"
            request = {runtime_key: kw.get(f"runtime{comp}", id)}
            if kw.get(f"job{comp}") not in ("global", "all"):
                request["job_id"] = kw.get(f"job{comp}", id)
            if kw.get(f"workflow_device{comp}"):
                request["workflow_device_id"] = kw.get(f"workflow_device{comp}")
        runs = fetch("Run", allow_none=True, **request)
        if not runs:
            return defaults
        return defaults + list(
            set(
                (result.device_id, result.device_name)
                for result in runs.results
                if result.device_id
            )
        )

    def get_job_list(self, id: int, **kw: Any) -> list:
        comp = "_compare" if kw["compare"] else ""
        defaults = [
            ("all", "All jobs"),
            ("all failed", "All jobs that failed"),
            ("all passed", "All jobs that passed"),
        ]
        return defaults + list(
            dict.fromkeys(
                (run.job_id, run.job.name)
                for run in sorted(
                    fetch(
                        "Run",
                        parent_runtime=kw.get(f"runtime{comp}"),
                        allow_none=True,
                        all_matches=True,
                    ),
                    key=attrgetter("runtime"),
                )
                if run.job_id
            )
        )

    def get_results(self, type: str, id: int, **kw: Any) -> Optional[dict]:
        comp = "_compare" if kw["compare"] else ""
        return getattr(self, f"get_{type}_results")(
            id,
            **{
                "runtime": kw.get(f"runtime{comp}"),
                "device": kw.get(f"device{comp}"),
                "job": kw.get(f"job{comp}"),
                "workflow_device": kw.get(f"workflow_device{comp}"),
            },
        )

    def get_run_results(self, id: int, device: Any, **kw: Any) -> Optional[dict]:
        run = fetch("Run", allow_none=True, id=id)
        return self.get_service_results(run.job.id, run.runtime, device, None, None)

    def get_device_results(self, id: int, runtime: str, **_: Any) -> Optional[dict]:
        run = fetch("Run", allow_none=True, runtime=runtime)
        return next(r.result for r in run.results if r.device_id == int(id))

    def get_workflow_results(
        self, id: int, runtime: str, device: Any, job: Any, workflow_device: Any
    ) -> Optional[dict]:
        if "all" not in job:
            return self.get_service_results(job, runtime, device, job, workflow_device)
        request = {"parent_runtime": runtime, "all_matches": True}
        if job in ("all passed", "all failed"):
            request["success"] = job == "all passed"
        return {
            run.job_name: next((r.result for r in run.results if not r.device_id), None)
            for run in fetch("Run", allow_none=True, **request)
            if run.job_id != int(id)
        }

    def get_service_results(
        self, id: int, runtime: str, device: Any, job: Any, workflow_device: Any
    ) -> Optional[dict]:
        runtime_key = "parent_runtime" if job else "runtime"
        request = {runtime_key: runtime, "job_id": id}
        if workflow_device:
            request["workflow_device_id"] = workflow_device
        run = fetch("Run", allow_none=True, **request)
        if not run:
            return None
        if "all" not in device:
            device_id = None if device == "global" else int(device)
            results = [r for r in run.results if device_id == r.device_id]
            return results[0].result if results else None
        else:
            return {
                r.device_name: r.result
                for r in run.results
                if r.device_id
                and (device == "all" or r.success == (device == "all passed"))
            }

    def compare_results(self, *args: Any, **kwargs: Any) -> dict:
        kwargs.pop("compare")
        first = self.str_dict(
            self.str_dict(self.get_results(*args, compare=False, **kwargs))
        ).splitlines()
        second = self.str_dict(
            self.get_results(*args, compare=True, **kwargs)
        ).splitlines()
        opcodes = SequenceMatcher(None, first, second).get_opcodes()
        return {"first": first, "second": second, "opcodes": opcodes}

    def add_restart_payload(self, job: Any, **kwargs: Any) -> dict:
        run = fetch(
            "Run", allow_none=True, job_id=job.id, runtime=kwargs.get("restart_runtime")
        )
        if not run:
            return {}
        result = [r for r in run.results if not r.device_id]
        payload = result[0].result["results"] if result else {}
        if not isinstance(payload, dict):
            return {}
        payload_jobs = set(payload) & set(kwargs.get("payloads_to_exclude", []))
        return {k: payload.get(k) for k in payload if k not in payload_jobs}

    @staticmethod
    def run(job: int, **kwargs: Any) -> dict:
        run_kwargs = {
            key: kwargs.pop(key)
            for key in ("creator", "runtime", "task", "restart_runtime")
            if kwargs.get(key)
        }
        run = factory("Run", job=job, **run_kwargs)
        run.properties = kwargs
        return run.run(kwargs.get("payload"))

    def run_job(self, id: Optional[int] = None, **kwargs: Any) -> dict:
        for property in ("user", "csrf_token", "form_type"):
            kwargs.pop(property, None)
        kwargs["creator"] = getattr(current_user, "name", "admin")
        job = fetch("Job", id=id)
        if job.type == "Workflow":
            if not kwargs.get("payload"):
                kwargs["payload"] = {}
            kwargs["payload"].update(self.add_restart_payload(job, **kwargs))
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
        workflow = fetch("Workflow", allow_none=True, id=workflow_id)
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
                job = fetch("Job", id=id)
                old_position = job.positions.get(workflow.name)
                job.positions[workflow.name] = new_position
            if new_position != old_position:
                workflow.last_modified = now
        return now

    def get_workflow_state(
        self, workflow_id: int, runtime: Optional[str] = None
    ) -> dict:
        workflow = fetch("Workflow", id=workflow_id)
        runtimes = [
            r.runtime
            for r in fetch("Run", allow_none=True, all_matches=True, job_id=workflow_id)
        ]
        state = None
        if runtime:
            state = self.run_db.get(runtime)
            if not state:
                results = fetch("Run", runtime=runtime).results
                global_result = [r for r in results if not r.device_id]
                state = global_result[0].result.get("state") if global_result else None
        return {"workflow": workflow.serialized, "runtimes": runtimes, "state": state}

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
            return getattr(fetch("Task", id=task_id), action)()
        except JobLookupError:
            return {"error": "This task no longer exists."}

    def scan_playbook_folder(self) -> list:
        path = Path(self.playbook_path or self.path / "playbooks")
        playbooks = [[str(f) for f in path.glob(e)] for e in ("*.yaml", "*.yml")]
        return sorted(sum(playbooks, []))
