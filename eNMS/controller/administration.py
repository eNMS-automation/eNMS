from copy import deepcopy
from datetime import datetime
from ipaddress import IPv4Network
from json import loads
from logging import info
from ldap3 import Connection, NTLM, SUBTREE
from os import makedirs
from os.path import exists
from requests import get as http_get
from typing import Any, Union
from yaml import dump, load, BaseLoader

from eNMS.controller.base import BaseController
from eNMS.database import Base
from eNMS.database.functions import delete_all, export, factory, fetch, fetch_all


class AdministrationController(BaseController):
    def authenticate_user(self, **kwargs: str) -> Base:
        name, password = kwargs["name"], kwargs["password"]
        if kwargs["authentication_method"] == "Local User":
            user = fetch("User", name=name)
            if user and password == user.password:
                return user
        elif kwargs["authentication_method"] == "LDAP Domain":
            with Connection(
                self.ldap_client,
                user=f"{self.ldap_userdn}\\{name}",
                password=password,
                auto_bind=True,
                authentication=NTLM,
            ) as connection:
                connection.search(
                    self.ldap_basedn,
                    f"(&(objectClass=person)(samaccountname={name}))",
                    search_scope=SUBTREE,
                    get_operational_attributes=True,
                    attributes=["cn", "memberOf", "mail"],
                )
                json_response = loads(connection.response_to_json())["entries"][0]
                if json_response:
                    user = {
                        "name": name,
                        "password": password,
                        "email": json_response["attributes"].get("mail", ""),
                    }
                    if any(
                        group in s
                        for group in self.ldap_admin_group.split(",")
                        for s in json_response["attributes"]["memberOf"]
                    ):
                        user["permissions"] = ["Admin"]
                    return factory("User", **user)
        elif kwargs["authentication_method"] == "TACACS":
            if self.tacacs_client.authenticate(name, password).valid:
                return factory("User", **{"name": name, "password": password})

    def database_helpers(self, **kwargs: Any) -> None:
        delete_all(*kwargs["deletion_types"])
        clear_logs_date = kwargs["clear_logs_date"]
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

    def migration_export(self, **kwargs: Union[list, str]) -> None:
        for cls_name in kwargs["import_export_types"]:
            path = self.path / "projects" / "migrations" / kwargs["name"]
            if not exists(path):
                makedirs(path)
            with open(path / f"{cls_name}.yaml", "w") as migration_file:
                dump(export(cls_name), migration_file, default_flow_style=False)

    def migration_import(self, **kwargs: Any) -> str:
        status, types = "Import successful.", kwargs["import_export_types"]
        workflows: list = []
        edges: list = []
        if kwargs.get("empty_database_before_import", False):
            delete_all(*types)
        for cls in types:
            path = (
                self.path / "projects" / "migrations" / kwargs["name"] / f"{cls}.yaml"
            )
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
        if kwargs.get("empty_database_before_import", False):
            self.create_default()
        return status

    def save_parameters(self, parameter_type: str, **kwargs: Any) -> None:
        self.update_parameters(**kwargs)
        if parameter_type == "git":
            self.get_git_content()

    def scan_cluster(self, **kwargs: Union[float, str]) -> None:
        protocol = self.parameters["cluster_scan_protocol"]
        for ip_address in IPv4Network(self.parameters["cluster_scan_subnet"]):
            try:
                server = http_get(
                    f"{protocol}://{ip_address}/rest/is_alive",
                    timeout=self.parameters["cluster_scan_timeout"],
                ).json()
                if self.cluster_id != server.pop("cluster_id"):
                    continue
                factory("Server", **{**server, **{"ip_address": str(ip_address)}})
            except ConnectionError:
                continue
