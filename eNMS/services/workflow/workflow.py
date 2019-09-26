from collections import defaultdict
from copy import deepcopy
from sqlalchemy import Boolean, ForeignKey, Integer
from sqlalchemy.orm import relationship
from time import sleep
from wtforms import BooleanField, HiddenField

from eNMS import app
from eNMS.database import Session
from eNMS.database.dialect import Column, MutableDict
from eNMS.database.functions import factory, fetch
from eNMS.database.associations import job_workflow_table, start_jobs_workflow_table
from eNMS.forms.automation import ServiceForm
from eNMS.forms.fields import MultipleInstanceField, NoValidationSelectField
from eNMS.models.automation import Service


class Workflow(Service):

    __tablename__ = "workflow"
    __mapper_args__ = {"polymorphic_identity": "workflow"}
    parent_type = "job"
    has_targets = Column(Boolean, default=True)
    id = Column(Integer, ForeignKey("job.id"), primary_key=True)
    labels = Column(MutableDict)
    jobs = relationship("Job", secondary=job_workflow_table, back_populates="workflows")
    edges = relationship(
        "WorkflowEdge", back_populates="workflow", cascade="all, delete-orphan"
    )
    start_jobs = relationship(
        "Job", secondary=start_jobs_workflow_table, backref="start_workflows"
    )

    def __init__(self, **kwargs):
        start, end = fetch("service", name="Start"), fetch("service", name="End")
        self.jobs.extend([start, end])
        super().__init__(**kwargs)
        if not kwargs.get("start_jobs"):
            self.start_jobs = [start]
        if self.name not in end.positions:
            end.positions[self.name] = (500, 0)

    def job(self, run, payload, device=None):
        run.set_state(progress_max=len(self.jobs))
        number_of_runs = defaultdict(int)
        jobs = list(run.start_jobs)
        payload = deepcopy(payload)
        visited = set()
        results = {"results": {}, "success": False, "runtime": run.runtime}
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
            elif device and job.python_query:
                try:
                    job_run = factory(
                        "run",
                        job=job.id,
                        workflow=self.id,
                        workflow_device=device.id,
                        parent_runtime=run.parent_runtime,
                        restart_run=run.restart_run,
                    )
                    job_run.properties = {}
                    result = job_run.run(payload)
                except Exception as exc:
                    result = {"success": False, "error": str(exc)}
                job_results = result
            else:
                job_run = factory(
                    "run",
                    job=job.id,
                    workflow=self.id,
                    parent_runtime=run.parent_runtime,
                    restart_run=run.restart_run,
                )
                job_run.properties = {"devices": [device.id]}
                Session.commit()
                job_results = job_run.run(payload)
            app.run_db[run.runtime]["jobs"][job.id]["success"] = job_results["success"]
            successors = []
            for successor, edge in job.adjacent_jobs(
                self, "destination", "success" if job_results["success"] else "failure"
            ):
                successors.append(successor)
                app.run_db[run.runtime]["edges"][edge.id] += 1
            payload[job.name] = job_results
            results["results"].update(payload)
            for successor in successors:
                jobs.append(successor)
                if successor == self.jobs[1]:
                    results["success"] = True
            if not skip_job and not job.skip:
                sleep(job.waiting_time)
        return results


class WorkflowForm(ServiceForm):
    form_type = HiddenField(default="payload_extraction_service")
    has_targets = BooleanField("Has Target Devices", default=True)
    start_jobs = MultipleInstanceField("Workflow Entry Point(s)")
    restart_runtime = NoValidationSelectField("Restart Runtime", choices=())
