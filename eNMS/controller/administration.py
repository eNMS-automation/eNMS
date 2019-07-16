from copy import deepcopy
from datetime import datetime
from flask_login import current_user
from ipaddress import IPv4Network
from json import loads
from logging import info
from ldap3 import Connection, NTLM, SUBTREE
from os import listdir, makedirs, scandir
from os.path import exists
from pathlib import Path
from requests import get as http_get
from typing import Any, Tuple, Union
from yaml import dump, load, BaseLoader

from eNMS.controller.base import BaseController
from eNMS.database import Base, Session
from eNMS.database.functions import delete_all, export, factory, fetch, fetch_all
from eNMS.models import relationships


class AdministrationController(BaseController):
    def authenticate_user(self, **kwargs: str) -> Base:
        name, password = kwargs["name"], kwargs["password"]
        if kwargs["authentication_method"] == "Local User":
            user = fetch("User", allow_none=True, name=name)
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
                    user = factory("User", **user)
        elif kwargs["authentication_method"] == "TACACS":
            if self.tacacs_client.authenticate(name, password).valid:
                user = factory("User", **{"name": name, "password": password})
        Session.commit()
        return user

    def get_user_credentials(self) -> Tuple[str, str]:
        return (current_user.name, current_user.password)

    def database_deletion(self, **kwargs: Any) -> None:
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

    def objectify(self, model: str, obj: dict) -> dict:
        for property, relation in relationships[model].items():
            if property not in obj:
                continue
            elif relation["list"]:
                obj[property] = [
                    fetch(relation["model"], name=name).id for name in obj[property]
                ]
            else:
                obj[property] = fetch(relation["model"], name=obj[property]).id
        return obj

    def migration_import(self, **kwargs: Any) -> str:
        status, types = "Import successful.", kwargs["import_export_types"]
        if kwargs.get("empty_database_before_import", False):
            for type in types:
                delete_all(type)
                Session.commit()
        workflow_edges: list = []
        for cls in types:
            path = (
                self.path / "projects" / "migrations" / kwargs["name"] / f"{cls}.yaml"
            )
            with open(path, "r") as migration_file:
                objects = load(migration_file, Loader=BaseLoader)
                if cls == "Workflow":
                    workflow_jobs = {
                        workflow["name"]: workflow.pop("jobs") for workflow in objects
                    }
                if cls == "WorkflowEdge":
                    workflow_edges = deepcopy(objects)
                if cls == "Service":
                    objects.sort(key=lambda s: s["type"] == "IterationService")
                for obj in objects:
                    obj_cls = obj.pop("type") if cls == "Service" else cls
                    obj = self.objectify(obj_cls, obj)
                    try:
                        factory(obj_cls, **obj)
                        Session.commit()
                    except Exception as e:
                        info(f"{str(obj)} could not be imported ({str(e)})")
                        status = "Partial import (see logs)."
        for name, jobs in workflow_jobs.items():
            fetch("Workflow", name=name).jobs = [
                fetch("Job", name=name) for name in jobs
            ]
            Session.commit()
        for edge in workflow_edges:
            for property in ("source", "destination", "workflow"):
                edge[property] = fetch("Job", name=edge[property]).id
            factory("WorkflowEdge", **edge)
            Session.commit()
        return status

    def import_jobs(self, **kwargs: Any) -> None:
        jobs = kwargs["jobs_to_import"]
        path = self.path / "projects" / "exported_jobs"
        for file in scandir(path / "services"):
            if file.name == ".gitkeep" or file.name not in jobs:
                continue
            with open(file.path, "r") as instance_file:
                instance = load(instance_file, Loader=BaseLoader)
                model = instance.pop("type")
                factory(model, **self.objectify(model, instance))
        Session.commit()
        for workflow in listdir(path / "workflows"):
            if workflow == ".gitkeep" or workflow not in jobs:
                continue
            for instance_type in ("jobs", "workflow", "edges"):
                path_job = path / "workflows" / workflow / instance_type
                for file in scandir(path_job):
                    with open(path_job / file.name, "r") as instance_file:
                        instance = load(instance_file, Loader=BaseLoader)
                        model = instance.pop("type")
                        factory(model, **self.objectify(model, instance))
                Session.commit()

    def export_job(self, job_id: str) -> None:
        job = fetch("Job", id=job_id)
        if job.type == "Workflow":
            path = self.path / "projects" / "exported_jobs" / "workflows" / job.name
            path.mkdir(parents=True, exist_ok=True)
            for instance_type in ("jobs", "workflow", "edges"):
                Path(path / instance_type).mkdir(parents=True, exist_ok=True)
            for sub_job in job.jobs:
                with open(path / "jobs" / f"{sub_job.name}.yaml", "w") as file:
                    sub_job_as_dict = sub_job.to_dict(export=True)
                    if sub_job.type == "Workflow":
                        sub_job_as_dict["type"] = "Workflow"
                    dump(sub_job_as_dict, file)
            for edge in job.edges:
                name = f"{edge.workflow}{edge.source}{edge.destination}"
                with open(path / "edges" / f"{name}.yaml", "w") as file:
                    edge = {**edge.to_dict(export=True), "type": "WorkflowEdge"}
                    dump(edge, file)
            with open(path / "workflow" / f"{job.name}.yaml", "w") as file:
                dump({**job.to_dict(export=True), "type": "Workflow"}, file)
        else:
            path = self.path / "projects" / "exported_jobs" / "services"
            with open(path / f"{job.name}.yaml", "w") as file:
                dump(job.to_dict(export=True), file)

    def get_exported_jobs(self) -> list:
        jobs_path = self.path / "projects" / "exported_jobs"
        return listdir(jobs_path / "services") + listdir(jobs_path / "workflows")

    def save_parameters(self, parameter_type: str, **kwargs: Any) -> None:
        self.update_parameters(**kwargs)
        if parameter_type == "git":
            self.get_git_content()

    def scan_cluster(self, **kwargs: Union[float, str]) -> None:
        for ip_address in IPv4Network(self.cluster_scan_subnet):
            try:
                server = http_get(
                    f"{self.cluster_scan_protocol}://{ip_address}/rest/is_alive",
                    timeout=self.cluster_scan_timeout,
                ).json()
                if self.cluster_id != server.pop("cluster_id"):
                    continue
                factory("Server", **{**server, **{"ip_address": str(ip_address)}})
            except ConnectionError:
                continue
