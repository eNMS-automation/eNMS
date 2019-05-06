from datetime import datetime
from difflib import SequenceMatcher
from flask import current_app, jsonify, request, send_file, session
from flask.wrappers import Response
from re import search, sub
from typing import Any, Dict

from eNMS.concurrent import threaded_job
from eNMS.controller import controller
from eNMS.forms.automation import WorkflowBuilderForm
from eNMS.database import delete, factory, fetch, fetch_all, get_one, objectify


class AutomationDispatcher:
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
        now = controller.get_time()
        fetch("Workflow", id=workflow_id).last_modified = now
        return {"edge": workflow_edge.serialized, "update_time": now}

    def add_jobs_to_workflow(self, workflow_id: int) -> Dict[str, Any]:
        workflow = fetch("Workflow", id=workflow_id)
        jobs = objectify("Job", request.form["add_jobs"])
        for job in jobs:
            job.workflows.append(workflow)
        now = controller.get_time()
        workflow.last_modified = now
        return {"jobs": [job.serialized for job in jobs], "update_time": now}

    def clear_results(self, job_id: int) -> None:
        fetch("Job", id=job_id).results = {}

    def delete_edge(self, workflow_id: int, edge_id: int) -> str:
        delete("WorkflowEdge", id=edge_id)
        now = controller.get_time()
        fetch("Workflow", id=workflow_id).last_modified = now
        return now

    def delete_node(self, workflow_id: int, job_id: int) -> dict:
        workflow, job = fetch("Workflow", id=workflow_id), fetch("Job", id=job_id)
        workflow.jobs.remove(job)
        now = controller.get_time()
        workflow.last_modified = now
        return {"job": job.serialized, "update_time": now}

    def download_configuration(self, name: str) -> Response:
        try:
            return send_file(
                filename_or_fp=str(
                    current_app.path / "git" / "configurations" / name / name
                ),
                as_attachment=True,
                attachment_filename=f"configuration_{name}.txt",
            )
        except FileNotFoundError:
            return jsonify("No configuration stored")

    def duplicate_workflow(self, workflow_id: int) -> dict:
        parent_workflow = fetch("Workflow", id=workflow_id)
        new_workflow = factory("Workflow", **request.form)
        for job in parent_workflow.jobs:
            new_workflow.jobs.append(job)
            job.positions[new_workflow.name] = job.positions[parent_workflow.name]
        for edge in parent_workflow.edges:
            subtype, src, destination = edge.subtype, edge.source, edge.destination
            new_workflow.edges.append(
                factory(
                    "WorkflowEdge",
                    **{
                        "name": (
                            f"{new_workflow.id}-{subtype}:",
                            f"{src.id}->{destination.id}",
                        ),
                        "workflow": new_workflow.id,
                        "subtype": subtype,
                        "source": src.id,
                        "destination": destination.id,
                    },
                )
            )
        return new_workflow.serialized

    def get_git_content(self) -> bool:
        parameters = get_one("Parameters")
        parameters.get_git_content(current_app)

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
        controller.scheduler.add_job(
            id=controller.get_time(),
            func=threaded_job,
            run_date=datetime.now(),
            args=[job.id],
            trigger="date",
        )
        return job.serialized

    def save_device_jobs(self, device_id: int) -> bool:
        fetch("Device", id=device_id).jobs = objectify("Job", request.form["jobs"])

    def save_positions(self, workflow_id: int) -> str:
        now = controller.get_time()
        workflow = fetch("Workflow", id=workflow_id)
        workflow.last_modified = now
        session["workflow"] = workflow.id
        for job_id, position in request.json.items():
            job = fetch("Job", id=job_id)
            job.positions[workflow.name] = (position["x"], position["y"])
        return now

    def get_results_diff(self, job_id: int, v1: str, v2: str) -> dict:
        job = fetch("Job", id=job_id)
        first = controller.str_dict(
            dict(reversed(sorted(job.results[v1].items())))
        ).splitlines()
        second = controller.str_dict(
            dict(reversed(sorted(job.results[v2].items())))
        ).splitlines()
        opcodes = SequenceMatcher(None, first, second).get_opcodes()
        return {"first": first, "second": second, "opcodes": opcodes}

    def calendar(self):
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
        return dict(tasks=tasks)

    def scheduler(self, action: str) -> bool:
        getattr(controller.scheduler, action)()

    def task_action(self, action: str, task_id: int) -> bool:
        getattr(fetch("Task", id=task_id), action)()

    def workflow_builder(self) -> dict:
        workflow = fetch("Workflow", id=session.get("workflow", None))
        return dict(
            workflow=workflow.serialized if workflow else None,
            workflow_builder_form=WorkflowBuilderForm(request.form),
        )
