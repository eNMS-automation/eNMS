from datetime import datetime
from flask import abort, current_app as app, redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user, login_required
from flask.wrappers import Response
from ldap3 import Connection, NTLM, SUBTREE
from os import listdir
from typing import Union

from eNMS.forms import (
    AdministrationForm,
    DatabaseHelpersForm,
    LoginForm,
    MigrationsForm,
)
from eNMS.framework import delete_all, factory, fetch, fetch_all, get_one
from eNMS.modules import (
    bp,
    db,
    ldap_client,
    scheduler,
    tacacs_client,
    USE_LDAP,
    USE_TACACS,
)


class AdministrationController:
    def administration(self) -> dict:
        return dict(
            form=AdministrationForm(request.form),
            parameters=get_one("Parameters").serialized,
        )

    def advanced(self) -> dict:
        return dict(
            database_helpers_form=DatabaseHelpersForm(request.form),
            migrations_form=MigrationsForm(request.form),
            folders=listdir(app.path / "migrations"),
        )

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

    def check_credentials(self):
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

    def login() -> Union[Response, str]:
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

    def logout() -> Response:
        logout_user()
        return redirect(url_for("bp.get_route"), endpoint="login")

    def save_parameters() -> bool:
        parameters = get_one("Parameters")
        parameters.update(**request.form)
        parameters.trigger_active_parameters(app)

    def scan_cluster() -> bool:
        parameters = get_one("Parameters")
        protocol = parameters.cluster_scan_protocol
        for ip_address in IPv4Network(parameters.cluster_scan_subnet):
            try:
                instance = http_get(
                    f"{protocol}://{ip_address}/rest/is_alive",
                    timeout=parameters.cluster_scan_timeout,
                ).json()
                if app.config["CLUSTER_ID"] != instance.pop("cluster_id"):
                    continue
                factory("Instance", **{**instance, **{"ip_address": str(ip_address)}})
            except ConnectionError:
                continue
