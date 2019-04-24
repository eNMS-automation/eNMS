from datetime import datetime
from flask import (
    abort,
    current_app as app,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
    session,
    url_for,
)
from flask.wrappers import Response
from typing import Any, Dict

from eNMS.framework import factory, fetch, fetch_all, objectify


class AutomationController:
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
        now = str(datetime.now())
        fetch("Workflow", id=workflow_id).last_modified = now
        return {"edge": workflow_edge.serialized, "update_time": now}

    def add_jobs_to_workflow(self, workflow_id: int) -> Dict[str, Any]:
        workflow = fetch("Workflow", id=workflow_id)
        jobs = objectify("Job", request.form["add_jobs"])
        for job in jobs:
            job.workflows.append(workflow)
        now = str(datetime.now())
        workflow.last_modified = now
        return {"jobs": [job.serialized for job in jobs], "update_time": now}

    def clear_results(job_id: int) -> None:
        fetch("Job", id=job_id).results = {}

    def delete_edge(self, workflow_id: int, edge_id: int) -> str:
        delete("WorkflowEdge", id=edge_id)
        now = str(datetime.now())
        fetch("Workflow", id=workflow_id).last_modified = now
        return now

    def delete_node(workflow_id: int, job_id: int) -> dict:
        workflow, job = fetch("Workflow", id=workflow_id), fetch("Job", id=job_id)
        workflow.jobs.remove(job)
        now = str(datetime.now())
        workflow.last_modified = now
        return {"job": job.serialized, "update_time": now}

    def download_configuration(name: str) -> Response:
        try:
            return send_file(
                filename_or_fp=str(app.path / "git" / "configurations" / name / name),
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
                        "name": f"{new_workflow.id}-{subtype}:{src.id}->{destination.id}",
                        "workflow": new_workflow.id,
                        "subtype": subtype,
                        "source": src.id,
                        "destination": destination.id,
                    },
                )
            )
        return new_workflow.serialized

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
