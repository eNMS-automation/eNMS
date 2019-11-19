from copy import deepcopy
from flask_login import current_user
from ipaddress import IPv4Network
from json import loads
from logging import info
from ldap3 import Connection, NTLM, SUBTREE
from os import listdir, makedirs
from os.path import exists
from pathlib import Path
from shutil import rmtree
from requests import get as http_get
from ruamel import yaml
from tarfile import open as open_tar
from traceback import format_exc

from eNMS.controller.base import BaseController
from eNMS.database import Session
from eNMS.database.functions import delete_all, export, factory, fetch, fetch_all
from eNMS.models import relationships


class AdministrationController(BaseController):
    def authenticate_user(self, **kwargs):
        name, password = kwargs["name"], kwargs["password"]
        if kwargs["authentication_method"] == "Local User":
            user = fetch("user", allow_none=True, name=name)
            return user if user and password == user.password else False
        elif kwargs["authentication_method"] == "LDAP Domain":
            with Connection(
                self.ldap_client,
                user=f"{self.config['ldap']['userdn']}\\{name}",
                password=password,
                auto_bind=True,
                authentication=NTLM,
            ) as connection:
                connection.search(
                    self.config["ldap"]["basedn"],
                    f"(&(objectClass=person)(samaccountname={name}))",
                    search_scope=SUBTREE,
                    get_operational_attributes=True,
                    attributes=["cn", "memberOf", "mail"],
                )
                json_response = loads(connection.response_to_json())["entries"][0]
                if json_response and any(
                    group in s
                    for group in self.config["ldap"]["admin_group"].split(",")
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

    def get_user_credentials(self):
        return (current_user.name, current_user.password)

    def database_deletion(self, **kwargs):
        delete_all(*kwargs["deletion_types"])

    def get_cluster_status(self):
        return {
            attr: [getattr(server, attr) for server in fetch_all("server")]
            for attr in ("status", "cpu_load")
        }

    def objectify(self, model, obj):
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

    def migration_import(self, folder="migrations", **kwargs):
        status, models = "Import successful.", kwargs["import_export_types"]
        if kwargs.get("empty_database_before_import", False):
            for model in models:
                delete_all(model)
                Session.commit()
        workflow_edges, workflow_services = [], {}
        folder_path = self.path / "files" / folder / kwargs["name"]
        for model in models:
            path = folder_path / f"{model}.yaml"
            if not path.exists():
                continue
            with open(path, "r") as migration_file:
                instances = yaml.load(migration_file)
                if model == "workflow_edge":
                    workflow_edges = deepcopy(instances)
                    continue
                for instance in instances:
                    instance_type = (
                        instance.pop("type") if model == "service" else model
                    )
                    if instance_type == "workflow":
                        workflow_services[instance["name"]] = instance.pop("services")
                    try:
                        instance = self.objectify(instance_type, instance)
                        factory(instance_type, **instance)
                        Session.commit()
                    except Exception:
                        info(
                            f"{str(instance)} could not be imported :"
                            f"{chr(10).join(format_exc().splitlines())}"
                        )
                        status = "Partial import (see logs)."
        try:
            for name, services in workflow_services.items():
                workflow = fetch("workflow", name=name)
                workflow.services = [
                    fetch("service", name=service_name) for service_name in services
                ]
            Session.commit()
            for edge in workflow_edges:
                for property in ("source", "destination", "workflow"):
                    edge[property] = fetch("service", name=edge[property]).id
                factory("workflow_edge", **edge)
                Session.commit()
            for service in fetch_all("service"):
                service.set_name()
            self.log("info", status)
        except Exception:
            info(chr(10).join(format_exc().splitlines()))
            status = "Partial import (see logs)."
        return status

    def import_service(self, archive):
        service_name = archive.split(".")[0]
        path = self.path / "files" / "services"
        with open_tar(path / archive) as tar_file:
            tar_file.extractall(path=path)
            status = self.migration_import(
                folder="services",
                name=service_name,
                import_export_types=["service", "workflow_edge"],
            )
        rmtree(path / service_name)
        return status

    def migration_export(self, **kwargs):
        for cls_name in kwargs["import_export_types"]:
            path = self.path / "files" / "migrations" / kwargs["name"]
            if not exists(path):
                makedirs(path)
            with open(path / f"{cls_name}.yaml", "w") as migration_file:
                yaml.dump(export(cls_name), migration_file)

    def export_service(self, service_id):
        service = fetch("service", id=service_id)
        path = Path(self.path / "files" / "services" / service.filename)
        path.mkdir(parents=True, exist_ok=True)
        services = service.deep_services if service.type == "workflow" else [service]
        services = [service.to_dict(export=True) for service in services]
        for service_dict in services:
            for relation in ("devices", "pools", "events"):
                service_dict.pop(relation)
        with open(path / "service.yaml", "w") as file:
            yaml.dump(services, file)
        if service.type == "workflow":
            with open(path / "workflow_edge.yaml", "w") as file:
                yaml.dump(
                    [edge.to_dict(export=True) for edge in service.deep_edges], file
                )
        with open_tar(f"{path}.tgz", "w:gz") as tar:
            tar.add(path, arcname=service.filename)
        rmtree(path, ignore_errors=True)

    def get_exported_services(self):
        return listdir(self.path / "files" / "services")

    def save_configuration(self, **config):
        self.config = config

    def scan_cluster(self, **kwargs):
        protocol = self.config["cluster"]["scan_protocol"]
        for ip_address in IPv4Network(self.config["cluster"]["scan_subnet"]):
            try:
                server = http_get(
                    f"{protocol}://{ip_address}/rest/is_alive",
                    timeout=self.config["cluster"]["scan_timeout"],
                ).json()
                if self.config["cluster"]["id"] != server.pop("cluster_id"):
                    continue
                factory("server", **{**server, **{"ip_address": str(ip_address)}})
            except ConnectionError:
                continue
