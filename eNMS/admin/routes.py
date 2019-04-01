from datetime import datetime
from flask import abort, current_app as app, redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user
from ipaddress import IPv4Network
from json import loads
from ldap3 import Connection, NTLM, SUBTREE
from logging import info
from os import listdir
from requests import get as rest_get
from requests.exceptions import ConnectionError
from typing import Union
from werkzeug.wrappers import Response

from eNMS.extensions import (
    db,
    ldap_client,
    scheduler,
    tacacs_client,
    USE_LDAP,
    USE_TACACS,
)
from eNMS.admin import bp
from eNMS.admin.forms import (
    AddInstance,
    AddUser,
    AdministrationForm,
    DatabaseHelpersForm,
    LoginForm,
    MigrationsForm,
)
from eNMS.admin.functions import migrate_export, migrate_import
from eNMS.functions import (
    delete_all,
    fetch_all,
    get,
    get_one,
    post,
    factory,
    fetch,
    serialize,
)
from eNMS.properties import instance_table_properties, user_table_properties


@get(bp, "/user_management", "View")
def user_management() -> dict:
    return dict(
        fields=user_table_properties,
        users=serialize("User"),
        form=AddUser(request.form),
    )


@get(bp, "/administration", "View")
def administration() -> dict:
    return dict(
        form=AdministrationForm(request.form),
        parameters=get_one("Parameters").serialized,
    )


@get(bp, "/advanced", "View")
def advanced() -> dict:
    return dict(
        database_helpers_form=DatabaseHelpersForm(request.form),
        migrations_form=MigrationsForm(request.form),
        folders=listdir(app.path / "migrations"),
    )


@get(bp, "/instance_management", "View")
def instance_management() -> dict:
    return dict(
        fields=instance_table_properties,
        instances=serialize("Instance"),
        form=AddInstance(request.form),
    )


@bp.route("/login", methods=["GET", "POST"])
def login() -> Union[Response, str]:
    if request.method == "POST":
        name, password = request.form["name"], request.form["password"]
        try:
            if request.form["authentication_method"] == "Local User":
                user = fetch("User", name=name)
                if user and password == user.password:
                    login_user(user)
                    return redirect(url_for("base_blueprint.dashboard"))
            elif request.form["authentication_method"] == "LDAP Domain":
                with Connection(
                    ldap_client,
                    user=f'{app.config["LDAP_USERDN"]}\\{name}',
                    password=password,
                    auto_bind=True,
                    authentication=NTLM,
                ) as connection:
                    connection.search(
                        app.config["LDAP_BASEDN"],
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
                            for group in app.config["LDAP_ADMIN_GROUP"]
                            for s in json_response["attributes"]["memberOf"]
                        ):
                            user["permissions"] = ["Admin"]
                        new_user = factory("User", **user)
                        login_user(new_user)
                        return redirect(url_for("base_blueprint.dashboard"))
            elif request.form["authentication_method"] == "TACACS":
                if tacacs_client.authenticate(name, password).valid:
                    user = factory("User", **{"name": name, "password": password})
                    login_user(user)
                    return redirect(url_for("base_blueprint.dashboard"))
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
    return redirect(url_for("base_blueprint.dashboard"))


@get(bp, "/logout")
def logout() -> Response:
    logout_user()
    return redirect(url_for("admin_blueprint.login"))


@post(bp, "/save_parameters", "Admin")
def save_parameters() -> bool:
    parameters = get_one("Parameters")
    parameters.update(**request.form)
    parameters.trigger_active_parameters(app)
    db.session.commit()
    return True


@post(bp, "/scan_cluster", "Admin")
def scan_cluster() -> bool:
    parameters = get_one("Parameters")
    protocol = parameters.cluster_scan_protocol
    for ip_address in IPv4Network(parameters.cluster_scan_subnet):
        try:
            instance = rest_get(
                f"{protocol}://{ip_address}/rest/is_alive",
                timeout=parameters.cluster_scan_timeout,
            ).json()
            if app.config["CLUSTER_ID"] != instance.pop("cluster_id"):
                continue
            factory("Instance", **{**instance, **{"ip_address": str(ip_address)}})
        except ConnectionError:
            continue
    db.session.commit()
    return True


@post(bp, "/get_cluster_status", "View")
def get_cluster_status() -> dict:
    instances = fetch_all("Instance")
    return {
        attr: [getattr(instance, attr) for instance in instances]
        for attr in ("status", "cpu_load")
    }


@post(bp, "/database_helpers", "Admin")
def database_helpers() -> bool:
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
        db.session.commit()
    return True


@post(bp, "/reset_status", "Admin")
def reset_status() -> bool:
    for job in fetch_all("Job"):
        job.is_running = False
    db.session.commit()
    return True


@post(bp, "/get_git_content", "Admin")
def git_action() -> bool:
    parameters = get_one("Parameters")
    parameters.get_git_content(app)
    return True


@post(bp, "/scheduler/<action>", "Admin")
def scheduler_action(action: str) -> bool:
    getattr(scheduler, action)()
    return True


@post(bp, "/migration_<direction>", "Admin")
def migration(direction: str) -> Union[bool, str]:
    args = (app, request.form)
    return migrate_import(*args) if direction == "import" else migrate_export(*args)
