from copy import deepcopy
from flask_login import current_user
from ipaddress import IPv4Network
from json import loads
from logging import info
from ldap3 import Connection, NTLM, SUBTREE
from os import listdir, makedirs, scandir
from os.path import exists
from pathlib import Path
from shutil import rmtree
from requests import get as http_get
from ruamel import yaml
from tarfile import open as open_tar
from typing import Any, Tuple, Union

from eNMS.controller.base import BaseController
from eNMS.database import Base, Session
from eNMS.database.functions import delete_all, export, factory, fetch, fetch_all
from eNMS.models import relationships


class AdministrationController(BaseController):
    def authenticate_user(self, **kwargs: str) -> Base:
        name, password = kwargs["name"], kwargs["password"]
        if kwargs["authentication_method"] == "Local User":
            user = fetch("user", allow_none=True, name=name)
            return user if user and password == user.password else False
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
                if json_response and any(
                    group in s
                    for group in self.ldap_admin_group.split(",")
                    for s in json_response["attributes"]["memberOf"]
                ):
                    user = factory(
                        "user",
                        **{
                            "name": name,
                            "password": password,
                            "email": json_response["attributes"].get("mail", ""),
                        },
                    )
        elif kwargs["authentication_method"] == "TACACS":
            if self.tacacs_client.authenticate(name, password).valid:
                user = factory("user", **{"name": name, "password": password})
        Session.commit()
        return user

    def get_user_credentials(self) -> Tuple[str, str]:
        return (current_user.name, current_user.password)

    def database_deletion(self, **kwargs: Any) -> None:
        delete_all(*kwargs["deletion_types"])

    def get_cluster_status(self) -> dict:
        return {
            attr: [getattr(server, attr) for server in fetch_all("server")]
            for attr in ("status", "cpu_load")
        }

    def migration_export(self, **kwargs: Any) -> None:
        for cls_name in kwargs["import_export_types"]:
            path = self.path / "projects" / "migrations" / kwargs["name"]
            if not exists(path):
                makedirs(path)
            with open(path / f"{cls_name}.yaml", "w") as migration_file:
                yaml.dump(export(cls_name), migration_file)

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
                objects = yaml.load(migration_file)
                if cls == "workflow":
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
                        if cls in ("Service", "workflow"):
                            Session.commit()
                        status = "Partial import (see logs)."
                    if cls not in ("Service", "workflow"):
                        Session.commit()
        for name, jobs in workflow_jobs.items():
            fetch("workflow", name=name).jobs = [
                fetch("Job", name=name) for name in jobs
            ]
            Session.commit()
        for edge in workflow_edges:
            for property in ("source", "destination", "workflow"):
                edge[property] = fetch("Job", name=edge[property]).id
            factory("workflow_edge", **edge)
            Session.commit()
        return status

    def import_jobs(self, **kwargs: Any) -> None:
        jobs = kwargs["jobs_to_import"]
        path = self.path / "projects" / "exported_jobs"
        for file in scandir(path / "services"):
            if file.name == ".gitkeep" or file.name not in jobs:
                continue
            with open(file.path, "r") as instance_file:
                instance = yaml.load(instance_file)
                model = instance.pop("type")
                factory(model, **self.objectify(model, instance))
        Session.commit()
        for workflow in listdir(path / "workflows"):
            if workflow == ".gitkeep" or workflow not in jobs:
                continue
            workflow_name = workflow.split(".")[0]
            with open_tar(path / "workflows" / workflow) as tar_file:
                tar_file.extractall(path=path / "workflows")
            for instance_type in ("jobs", "workflow", "edges"):
                path_job = path / "workflows" / workflow_name / instance_type
                for file in scandir(path_job):
                    with open(path_job / file.name, "r") as instance_file:
                        instance = yaml.load(instance_file)
                        model = instance.pop("type")
                        factory(model, **self.objectify(model, instance))
                Session.commit()
            rmtree(path / "workflows" / workflow_name)

    def export_job(self, job_id: str) -> None:
        job = fetch("Job", id=job_id)
        if job.type == "workflow":
            path = self.path / "projects" / "exported_jobs" / "workflows" / job.filename
            path.mkdir(parents=True, exist_ok=True)
            for instance_type in ("jobs", "workflow", "edges"):
                Path(path / instance_type).mkdir(parents=True, exist_ok=True)
            for sub_job in job.jobs:
                with open(path / "jobs" / f"{sub_job.filename}.yaml", "w") as file:
                    sub_job_as_dict = sub_job.to_dict(export=True)
                    for relation in ("devices", "pools", "events"):
                        sub_job_as_dict.pop(relation)
                    if sub_job.type == "workflow":
                        sub_job_as_dict["type"] = "Workflow"
                    yaml.dump(sub_job_as_dict, file)
            for edge in job.edges:
                name = self.strip_all(f"{edge.workflow}{edge.source}{edge.destination}")
                with open(path / "edges" / f"{name}.yaml", "w") as file:
                    edge = {**edge.to_dict(export=True), "type": "WorkflowEdge"}
                    yaml.dump(edge, file)
            with open(path / "workflow" / f"{job.filename}.yaml", "w") as file:
                job_as_dict = job.to_dict(export=True)
                for relation in ("devices", "pools", "events"):
                    job_as_dict.pop(relation)
                yaml.dump({**job_as_dict, "type": "Workflow"}, file)
            with open_tar(f"{path}.tgz", "w:gz") as tar:
                tar.add(path, arcname=job.filename)
            rmtree(path)
        else:
            path = self.path / "projects" / "exported_jobs" / "services"
            with open(path / f"{job.filename}.yaml", "w") as file:
                job_as_dict = job.to_dict(export=True)
                for relation in ("devices", "pools", "events"):
                    job_as_dict.pop(relation)
                yaml.dump(job_as_dict, file)

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
                factory("server", **{**server, **{"ip_address": str(ip_address)}})
            except ConnectionError:
                continue
