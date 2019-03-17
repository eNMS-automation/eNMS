from datetime import datetime
from difflib import SequenceMatcher
from flask import request, session
from json import dumps
from sqlalchemy.exc import DataError
from typing import List

from eNMS.extensions import db, scheduler
from eNMS.automation.functions import scheduler_job
from eNMS.base.classes import service_classes
from eNMS.base.functions import (
    delete,
    factory,
    fetch,
    get,
    objectify,
    post,
    str_dict,
    serialize,
)
from eNMS.base.properties import (
    cls_to_properties,
    pretty_names,
    private_properties,
    property_types,
    service_table_properties,
    workflow_table_properties,
)
from eNMS.automation import bp
from eNMS.automation.forms import (
    AddJobForm,
    CompareLogsForm,
    JobForm,
    WorkflowBuilderForm,
)


@get(bp, "/service_management", "View")
def service_management() -> dict:
    return dict(
        compare_logs_form=CompareLogsForm(request.form),
        fields=service_table_properties,
        service_form=JobForm(request.form),
        services_classes=list(service_classes),
        services=serialize("Service"),
    )


@get(bp, "/workflow_management", "View")
def workflow_management() -> dict:
    return dict(
        compare_logs_form=CompareLogsForm(request.form),
        fields=workflow_table_properties,
        workflows=serialize("Workflow"),
        workflow_creation_form=JobForm(request.form),
    )


@get(bp, "/workflow_builder", "View")
def workflow_builder() -> dict:
    workflow = fetch("Workflow", id=session.get("workflow", None))
    return dict(
        workflow=workflow.serialized if workflow else None,
        add_job_form=AddJobForm(request.form),
        workflow_builder_form=WorkflowBuilderForm(request.form),
        workflow_creation_form=JobForm(request.form),
        compare_logs_form=CompareLogsForm(request.form),
        service_form=JobForm(request.form),
        services_classes=list(service_classes),
    )


@get(bp, "/detach_logs/<int:id>", "View")
def detached_logs(id: int) -> dict:
    return {"job": id, "compare_logs_form": CompareLogsForm(request.form)}


@get(bp, "/logs/<int:id>/<runtime>", "View")
def logs(id: int, runtime: str) -> str:
    job = fetch("Job", id=id)
    if not job:
        message = "The associated job has been deleted."
    else:
        message = job.logs.get(runtime, "Logs have been removed")
    return f"<pre>{dumps(message, indent=4)}</pre>"


@post(bp, "/get_logs/<int:id>", "View")
def get_logs(id: int) -> dict:
    return fetch("Job", id=id).logs


@post(bp, "/get_service/<id_or_cls>", "View")
def get_service(id_or_cls: str) -> dict:
    service = None
    try:
        service = fetch("Service", id=id_or_cls)
    except DataError:
        pass
    cls = service_classes[service.type if service else id_or_cls]

    def build_text_box(property: str, name: str) -> str:
        return f"""
            <label>{name}</label>
            <div class="form-group">
              <input class="form-control" id="service-{property}"
              maxlength="{getattr(cls, f'{property}_length', 524288)}"
              name="{property}" type="{'password'
              if property in private_properties else 'text'}">
            </div>"""

    def build_textarea_box(property: str, name: str) -> str:
        return f"""
            <label>{name}</label>
            <div class="form-group">
              <textarea style="height: 150px;" rows="30"
              maxlength="{getattr(cls, f'{property}_length', 524288)}"
              class="form-control" id="service-{property}"
              name="{property}"></textarea>
            </div>"""

    def build_select_box(property: str, name: str) -> str:
        options = "".join(
            f'<option value="{k}">{v}</option>'
            for k, v in getattr(cls, f"{property}_values")
        )
        return f"""
            <label>{name}</label>
            <div class="form-group">
              <select class="form-control"
                id="service-{property}" name="{property}"
                {'multiple size="7"'
                if property_types[property] == 'list'
                else ''}>{options}
              </select>
            </div>"""

    def build_boolean_box(property: str, name: str) -> str:
        return (
            "<fieldset>"
            + f"""
            <div class="item">
                <input id="service-{property}" name="{property}"
                type="checkbox"><label>{name}</label>
            </div>"""
            + "</fieldset>"
        )

    form, list_properties, boolean_properties = "", [], []
    for property in cls_to_properties[cls.__tablename__]:
        name = pretty_names.get(property, property)
        if property in cls_to_properties["Service"]:
            continue
        if property_types.get(property, None) == "bool":
            form += build_boolean_box(property, name)
            boolean_properties.append(property)
        elif hasattr(cls, f"{property}_values"):
            form += build_select_box(property, name)
            if property_types[property] == "list":
                list_properties.append(property)
        elif hasattr(cls, f"{property}_textarea"):
            form += build_textarea_box(property, name)
        else:
            form += build_text_box(property, name)
    return {
        "boolean_properties": ",".join(boolean_properties),
        "form": form,
        "list_properties": ",".join(list_properties),
        "service": service.serialized if service else None,
    }


@post(bp, "/run_job/<int:job_id>", "Edit")
def run_job(job_id: int) -> dict:
    job = fetch("Job", id=job_id)
    if job.is_running:
        return {"error": "Job is already running."}
    targets = job.compute_targets()
    if hasattr(job, "has_targets"):
        if job.has_targets and not targets:
            return {"error": "Set devices or pools as targets first."}
        if not job.has_targets and targets:
            return {"error": "This service should not have targets configured."}
    scheduler.add_job(
        id=str(datetime.now()),
        func=scheduler_job,
        run_date=datetime.now(),
        args=[job.id],
        trigger="date",
    )
    return job.serialized


@post(bp, "/get_diff/<int:job_id>/<v1>/<v2>", "View")
def get_diff(job_id: int, v1: str, v2: str) -> dict:
    job = fetch("Job", id=job_id)
    first = str_dict(job.logs[v1]).splitlines()
    second = str_dict(job.logs[v2]).splitlines()
    opcodes = SequenceMatcher(None, first, second).get_opcodes()
    return {"first": first, "second": second, "opcodes": opcodes}


@post(bp, "/clear_logs/<int:job_id>", "Edit")
def clear_logs(job_id: int) -> bool:
    fetch("Job", id=job_id).logs = {}
    db.session.commit()
    return True


@post(bp, "/add_jobs_to_workflow/<int:workflow_id>", "Edit")
def add_jobs_to_workflow(workflow_id: int) -> List[dict]:
    workflow = fetch("Workflow", id=workflow_id)
    jobs = objectify("Job", request.form["add_jobs"])
    for job in jobs:
        job.workflows.append(workflow)
    workflow.last_modified = str(datetime.now())
    db.session.commit()
    return [job.serialized for job in jobs]


@post(bp, "/duplicate_workflow/<int:workflow_id>", "Edit")
def duplicate_workflow(workflow_id: int) -> dict:
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
    db.session.commit()
    return new_workflow.serialized


@post(bp, "/reset_workflow_logs/<int:workflow_id>", "Edit")
def reset_workflow_logs(workflow_id: int) -> bool:
    fetch("Workflow", id=workflow_id).state = {}
    db.session.commit()
    return True


@post(bp, "/delete_node/<int:workflow_id>/<int:job_id>", "Edit")
def delete_node(workflow_id: int, job_id: int) -> dict:
    workflow, job = fetch("Workflow", id=workflow_id), fetch("Job", id=job_id)
    workflow.jobs.remove(job)
    workflow.last_modified = str(datetime.now())
    db.session.commit()
    return job.serialized


@post(bp, "/add_edge/<int:workflow_id>/<subtype>/<int:source>/<int:dest>", "Edit")
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
    fetch("Workflow", id=workflow_id).last_modified = str(datetime.now())
    db.session.commit()
    return workflow_edge.serialized


@post(bp, "/delete_edge/<int:workflow_id>/<int:edge_id>", "Edit")
def delete_edge(workflow_id: int, edge_id: int) -> dict:
    fetch("Workflow", id=workflow_id).last_modified = str(datetime.now())
    db.session.commit()
    return delete("WorkflowEdge", id=edge_id)


@post(bp, "/save_positions/<int:workflow_id>", "Edit")
def save_positions(workflow_id: int) -> bool:
    workflow = fetch("Workflow", id=workflow_id)
    session["workflow"] = workflow.id
    for job_id, position in request.json.items():
        job = fetch("Job", id=job_id)
        job.positions[workflow.name] = (position["x"], position["y"])
    db.session.commit()
    return True
