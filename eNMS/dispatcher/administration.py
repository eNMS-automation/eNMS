from copy import deepcopy
from datetime import datetime
from flask import abort, current_app, redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user
from flask.wrappers import Response
from ipaddress import IPv4Network
from json import loads
from logging import info
from ldap3 import Connection, NTLM, SUBTREE
from os import listdir, makedirs
from os.path import exists
from requests import get as http_get
from typing import Union
from yaml import dump, load, BaseLoader

from eNMS.default import create_default
from eNMS.forms.administration import LoginForm
from eNMS.database import delete_all, export, factory, fetch, fetch_all, get_one
from eNMS.modules import ldap_client, tacacs_client, USE_LDAP, USE_TACACS


class AdministrationDispatcher:
    def administration(self) -> dict:
        return dict(folders=listdir(current_app.path / "migrations"))

    def database_helpers(self) -> None:
        delete_all(*request.form["deletion_types"])
        clear_logs_date = request.form["clear_logs_date"]
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

    def login(self) -> Union[Response, str]:
        if request.method == "POST":
            name, password = request.form["name"], request.form["password"]
            try:
                if request.form["authentication_method"] == "Local User":
                    user = fetch("User", name=name)
                    if user and password == user.password:
                        login_user(user)
                        return redirect(url_for("bp.get_route", page="dashboard"))
                elif request.form["authentication_method"] == "LDAP Domain":
                    with Connection(
                        ldap_client,
                        user=f'{current_app.config["LDAP_USERDN"]}\\{name}',
                        password=password,
                        auto_bind=True,
                        authentication=NTLM,
                    ) as connection:
                        connection.search(
                            current_app.config["LDAP_BASEDN"],
                            f"(&(objectClass=person)(samaccountname={name}))",
                            search_scope=SUBTREE,
                            get_operational_attributes=True,
                            attributes=["cn", "memberOf", "mail"],
                        )
                        json_response = loads(connection.response_to_json())["entries"][
                            0
                        ]
                        if json_response:
                            user = {
                                "name": name,
                                "password": password,
                                "email": json_response["attributes"].get("mail", ""),
                            }
                            if any(
                                group in s
                                for group in current_app.config["LDAP_ADMIN_GROUP"]
                                for s in json_response["attributes"]["memberOf"]
                            ):
                                user["permissions"] = ["Admin"]
                            new_user = factory("User", **user)
                            login_user(new_user)
                            return redirect(url_for("bp.get_route", page="dashboard"))
                elif request.form["authentication_method"] == "TACACS":
                    if tacacs_client.authenticate(name, password).valid:
                        user = factory("User", **{"name": name, "password": password})
                        login_user(user)
                        return redirect(url_for("bp.get_route", page="dashboard"))
                abort(403)
            except Exception as e:
                info(f"Authentication failed ({str(e)})")
                abort(403)
        if not current_user.is_authenticated:
            login_form = LoginForm(request.form)
            authentication_methods = [("Local User",) * 2]
            if USE_LDAP:
                authentication_methods.append(("LDAP Domain",) * 2)
            if USE_TACACS:
                authentication_methods.append(("TACACS",) * 2)
            login_form.authentication_method.choices = authentication_methods
            return render_template("login.html", login_form=login_form)
        return redirect(url_for("bp.get_route", page="dashboard"))

    def logout(self) -> Response:
        logout_user()
        return redirect(url_for("bp.get_route", page="login"))

    def migration_export(self) -> None:
        for cls_name in request.form["import_export_types"]:
            path = current_app.path / "migrations" / request.form["name"]
            if not exists(path):
                makedirs(path)
            with open(path / f"{cls_name}.yaml", "w") as migration_file:
                dump(export(cls_name), migration_file, default_flow_style=False)

    def migration_import(self) -> str:
        status, types = "Import successful.", request.form["import_export_types"]
        workflows: list = []
        edges: list = []
        if request.form.get("empty_database_before_import", False):
            delete_all(*types)
        for cls in types:
            path = (
                current_app.path / "migrations" / request.form["name"] / f"{cls}.yaml"
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
        if request.form.get("empty_database_before_import", False):
            create_default(current_app)
        return status

    def save_parameters(self, parameter_type) -> bool:
        parameters = get_one("Parameters")
        parameters.update(**request.form)
        if parameter_type == "git":
            parameters.get_git_content(current_app)

    def scan_cluster(self) -> bool:
        parameters = get_one("Parameters")
        protocol = parameters.cluster_scan_protocol
        for ip_address in IPv4Network(parameters.cluster_scan_subnet):
            try:
                server = http_get(
                    f"{protocol}://{ip_address}/rest/is_alive",
                    timeout=parameters.cluster_scan_timeout,
                ).json()
                if current_app.config["CLUSTER_ID"] != server.pop("cluster_id"):
                    continue
                factory("Server", **{**server, **{"ip_address": str(ip_address)}})
            except ConnectionError:
                continue
