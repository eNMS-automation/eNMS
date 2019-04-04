from copy import deepcopy
from flask import Flask
from logging import info
from os import makedirs
from os.path import exists
from uuid import getnode
from yaml import dump, load, BaseLoader

from eNMS.default import create_default
from eNMS.functions import delete_all, export, factory


def configure_instance_id() -> None:
    factory(
        "Instance",
        **{
            "name": str(getnode()),
            "description": "Localhost",
            "ip_address": "0.0.0.0",
            "status": "Up",
        },
    )


def migrate_export(app: Flask, request: dict) -> bool:
    for cls_name in request["import_export_types"]:
        path = app.path / "migrations" / request["name"]
        if not exists(path):
            makedirs(path)
        with open(path / f"{cls_name}.yaml", "w") as migration_file:
            dump(export(cls_name), migration_file, default_flow_style=False)
    return True


def migrate_import(app: Flask, request: dict) -> str:
    status, types = "Import successful.", request["import_export_types"]
    workflows: list = []
    edges: list = []
    if request.get("empty_database_before_import", False):
        delete_all(*types)
    for cls in types:
        path = app.path / "migrations" / request["name"] / f"{cls}.yaml"
        with open(path, "r") as migration_file:
            objects = load(migration_file, Loader=BaseLoader)
            if cls == "Workflow":
                workflows = deepcopy(objects)
            if cls == "WorkflowEdge":
                edges = deepcopy(objects)
                continue
            for obj in objects:
                obj_cls = obj.pop("type") if cls == "Service" else cls
                # 1) We cannot import workflow edges before workflow, because a
                # workflow edge is defined by the workflow it belongs to.
                # Therefore, we import workflow before workflow edges but
                # strip off the edges, because they do not exist at this stage.
                # Edges will be defined later on upon importing workflow edges.
                # 2) At this stage, we cannot import jobs, because if workflows
                # A (ID 1) and B (ID 2) are created, and B is added to A as a
                # subworkflow, we won't be able to create A as B is one of its
                # jobs and does not exist yet. To work around this, we will
                # strip off the jobs at this stage, and reimport workflows a
                # second time at the end.
                if cls == "Workflow":
                    obj["edges"], obj["jobs"] = [], []
                try:
                    factory(obj_cls, **obj)
                except Exception as e:
                    info(f"{str(obj)} could not be imported ({str(e)})")
                    status = "Partial import (see logs)."
    for workflow in workflows:
        workflow["edges"] = []
        try:
            factory("Workflow", **workflow)
        except Exception as e:
            info(f"{str(workflow)} could not be imported ({str(e)})")
            status = "Partial import (see logs)."
    for edge in edges:
        try:
            factory("WorkflowEdge", **edge)
        except Exception as e:
            info(f"{str(edge)} could not be imported ({str(e)})")
            status = "Partial import (see logs)."
    if request.get("empty_database_before_import", False):
        create_default(app)
    return status
