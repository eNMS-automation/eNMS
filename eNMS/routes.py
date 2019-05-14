from flask import (
    abort,
    current_app,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
    session,
    url_for,
)
from flask_login import current_user
from flask_wtf import FlaskForm
from flask.wrappers import Response
from json.decoder import JSONDecodeError
from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError
from typing import List
from werkzeug.wrappers.response import Response

from eNMS.controller import controller
from eNMS.database import Session
from eNMS.database.functions import delete, factory, fetch, fetch_all, Session
from eNMS.forms import form_actions, form_classes, form_postprocessing, form_templates
from eNMS.forms.administration import LoginForm
from eNMS.forms.automation import ServiceTableForm
from eNMS.extensions import bp, cache
from eNMS.models import models
from eNMS.properties.diagram import type_to_diagram_properties
from eNMS.properties.table import (
    filtering_properties,
    table_fixed_columns,
    table_properties,
)


@bp.route("/")
def site_root() -> Response:
    return redirect(url_for("bp.route", page="login"))


@bp.route("/filtering")
def filtering(table: str) -> dict:
    model = models.get(table, models["Device"])
    properties = table_properties[table]
    try:
        order_property = properties[int(request.args["order[0][column]"])]
    except IndexError:
        order_property = "name"
    order = getattr(getattr(model, order_property), request.args["order[0][dir]"])()
    constraints = []
    for property in filtering_properties[table]:
        value = request.args.get(f"form[{property}]")
        if value:
            constraints.append(getattr(model, property).contains(value))
    result = Session.query(model).filter(and_(*constraints)).order_by(order)
    if table in ("device", "link", "configuration"):
        pools = [int(id) for id in request.args.getlist("form[pools][]")]
        if pools:
            result = result.filter(model.pools.any(models["pool"].id.in_(pools)))
    return {
        "jsonify": True,
        "draw": int(request.args["draw"]),
        "recordsTotal": len(Session.query(model).all()),
        "recordsFiltered": len(result.all()),
        "data": [
            [getattr(obj, property) for property in properties]
            + obj.generate_row(table)
            for obj in result.limit(int(request.args["length"]))
            .offset(int(request.args["start"]))
            .all()
        ],
    }


@bp.route("/form-<form_type>")
def form(form_type: str) -> dict:
    return render_template(
        f"forms/{form_templates.get(form_type, 'base')}_form.html"
        ** {
            "endpoint": "dashboard",
            "action": form_actions.get(form_type),
            "form": form_actions.get(form_type),
            "form_type": form_type,
        }
    )


@bp.route("/table-<table_type>")
def table(table_type: str) -> dict:
    table_dict = dict(
        properties=table_properties[table_type],
        fixed_columns=table_fixed_columns[table_type],
        type=table_type,
        template="pages/table",
    )
    if table_type == "service":
        service_table_form = ServiceTableForm(request.form)
        service_table_form.services.choices = [
            (service, service)
            for service in models
            if service != "Service" and service.endswith("Service")
        ]
        table_dict["service_table_form"] = service_table_form
    return table_dict


@bp.route("/dashboard")
def dashboard() -> dict:
    return render_template(
        f"pages/dashboard.html",
        **{"endpoint": "dashboard", "properties": type_to_diagram_properties},
    )


@bp.route("/workflow_builder")
def workflow_builder() -> dict:
    workflow = fetch("Workflow", id=session.get("workflow", None))
    return dict(workflow=workflow.serialized if workflow else None)


@bp.route("/calendar")
def calendar() -> dict:
    return {}


@bp.route("/download_configuration-<name>")
def download_configuration(name: str) -> Response:
    try:
        return send_file(
            filename_or_fp=str(
                current_app.path / "git" / "configurations" / name / name
            ),
            as_attachment=True,
            attachment_filename=f"configuration_{name}.txt",
        )
    except FileNotFoundError:
        return jsonify("No configuration stored")


@bp.route("/administration")
def administration() -> dict:
    return render_template(
        f"administration.html",
        **{"endpoint": page, "folders": listdir(current_app.path / "migrations")},
    )


@bp.route("/login", methods=["GET", "POST"])
def login() -> Response:
    if request.method == "POST":
        name, password = request.form["name"], request.form["password"]
        try:
            if request.form["authentication_method"] == "Local User":
                user = fetch("User", name=name)
                if user and password == user.password:
                    login_user(user)
                    return redirect(url_for("bp.route", page="dashboard"))
            elif request.form["authentication_method"] == "LDAP Domain":
                with Connection(
                    controller.ldap_client,
                    user=f"{controller.LDAP_USERDN}\\{name}",
                    password=password,
                    auto_bind=True,
                    authentication=NTLM,
                ) as connection:
                    connection.search(
                        controller.LDAP_BASEDN,
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
                            for group in controller.LDAP_ADMIN_GROUP
                            for s in json_response["attributes"]["memberOf"]
                        ):
                            user["permissions"] = ["Admin"]
                        new_user = factory("User", **user)
                        login_user(new_user)
                        return redirect(url_for("bp.route", page="dashboard"))
            elif request.form["authentication_method"] == "TACACS":
                if controller.tacacs_client.authenticate(name, password).valid:
                    user = factory("User", **{"name": name, "password": password})
                    login_user(user)
                    return redirect(url_for("bp.route", page="dashboard"))
            abort(403)
        except Exception as e:
            info(f"Authentication failed ({str(e)})")
            abort(403)
    if not current_user.is_authenticated:
        login_form = LoginForm(request.form)
        authentication_methods = [("Local User",) * 2]
        if controller.USE_LDAP:
            authentication_methods.append(("LDAP Domain",) * 2)
        if controller.USE_TACACS:
            authentication_methods.append(("TACACS",) * 2)
        login_form.authentication_method.choices = authentication_methods
        return render_template("login.html", login_form=login_form)
    return redirect(url_for("bp.route", page="dashboard"))


@bp.route("/logout")
def logout() -> Response:
    logout_user()
    return redirect(url_for("bp.route", page="login"))


@bp.route("/<page>", methods=["GET", "POST"])
@cache.cached(timeout=0, unless=controller.unless_cache)
def route(page: str) -> Response:
    if not current_user.is_authenticated:
        controller.log(
            "warning",
            (
                f"Unauthenticated {request.method} request from "
                f"'{request.remote_addr}' calling the endpoint '{request.url}'"
            ),
        )
        if request.method == "POST":
            return dispatcher.login() if page == "login" else False
        if request.method == "GET" and page != "login":
            return current_app.login_manager.unauthorized()
    func, *args = page.split("-")

    if request.method == "POST":
        form_type = request.form.get("form_type")
        if form_type:
            form = form_classes[form_type](request.form)
            if not form.validate_on_submit():
                return jsonify({"invalid_form": True, **{"errors": form.errors}})
            request.form = form_postprocessing(request.form)
    # try:
    # if not hasattr(dispatcher, func):
    #    abort(404)
    result = getattr(controller, func)(*args)
    Session.commit()
    # except Exception as e:
    # result = {"error": str(e)}
    if isinstance(result, Response) or isinstance(result, str):
        return result
    elif request.method == "POST" or func == "filtering":
        return jsonify(result)
