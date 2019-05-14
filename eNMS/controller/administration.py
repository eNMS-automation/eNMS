from copy import deepcopy
from datetime import datetime
from flask import abort, current_app, redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user
from ipaddress import IPv4Network
from json import loads
from logging import info
from ldap3 import Connection, NTLM, SUBTREE
from os import listdir, makedirs
from os.path import exists
from requests import get as http_get
from werkzeug.wrappers import Response
from yaml import dump, load, BaseLoader

from eNMS.database.default import create_default
from eNMS.database.functions import (
    delete_all,
    export,
    factory,
    fetch,
    fetch_all,
    get_one,
)


class AdministrationController:
    def database_helpers(self) -> None:
        delete_all(*parameters["deletion_types"])
        clear_logs_date = parameters["clear_logs_date"]
        if clear_logs_date:
            clear_date = datetime.strptime(clear_logs_date, "%d/%m/%Y %H:%M:%S")
            for job in fetch_all("Job"):
                job.logs = {
                    date: log
                    for date, log in job.logs.items()
                    if datetime.strptime(date, "%Y-%m-%d-%H:%M:%S.%f") > clear_date
                }

    def get_cluster_status(self) -> dict:
        return {
            attr: [getattr(server, attr) for server in fetch_all("Server")]
            for attr in ("status", "cpu_load")
        }

    def migration_export(self) -> None:
        for cls_name in parameters["import_export_types"]:
            path = current_app.path / "migrations" / parameters["name"]
            if not exists(path):
                makedirs(path)
            with open(path / f"{cls_name}.yaml", "w") as migration_file:
                dump(export(cls_name), migration_file, default_flow_style=False)

    def migration_import(self) -> str:
        status, types = "Import successful.", parameters["import_export_types"]
        workflows: list = []
        edges: list = []
        if parameters.get("empty_database_before_import", False):
            delete_all(*types)
        for cls in types:
            path = current_app.path / "migrations" / parameters["name"] / f"{cls}.yaml"
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
        if parameters.get("empty_database_before_import", False):
            create_default(current_app)
        return status

    def save_parameters(self, parameter_type: str) -> None:
        parameters = get_one("Parameters")
        parameters.update(**parameters)
        if parameter_type == "git":
            parameters.get_git_content(current_app)

    def scan_cluster(self) -> None:
        parameters = get_one("Parameters")
        protocol = parameters.cluster_scan_protocol
        for ip_address in IPv4Network(parameters.cluster_scan_subnet):
            try:
                server = http_get(
                    f"{protocol}://{ip_address}/rest/is_alive",
                    timeout=parameters.cluster_scan_timeout,
                ).json()
                if self.config["CLUSTER_ID"] != server.pop("cluster_id"):
                    continue
                factory("Server", **{**server, **{"ip_address": str(ip_address)}})
            except ConnectionError:
                continue
