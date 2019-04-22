from datetime import datetime
from typing import Any, Dict

from eNMS.framework import factory, fetch, objectify


class AutomationController:
    def add_edge(workflow_id: int, subtype: str, source: int, dest: int) -> dict:
        workflow_edge = factory(
            "WorkflowEdge",
            **{
                "name": f"{workflow_id}-{subtype}:{source}->{dest}",
                "workflow": workflow_id,
                "subtype": subtype,
                "source": source,
                "destination": dest,
            },
        )
        now = str(datetime.now())
        fetch("Workflow", id=workflow_id).last_modified = now
        db.session.commit()
        return {"edge": workflow_edge.serialized, "update_time": now}

    def add_jobs_to_workflow(self, workflow_id: int, form: dict) -> Dict[str, Any]:
        workflow = fetch("Workflow", id=workflow_id)
        jobs = objectify("Job", form["add_jobs"])
        for job in jobs:
            job.workflows.append(workflow)
        now = str(datetime.now())
        workflow.last_modified = now
        return {"jobs": [job.serialized for job in jobs], "update_time": now}
