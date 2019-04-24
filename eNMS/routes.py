from collections import Counter
from datetime import datetime
from difflib import SequenceMatcher
from flask import (
    abort,
    current_app as app,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
    session,
    url_for,
)
from flask_login import current_user, login_user, logout_user
from flask_login import current_user, login_required
from flask_wtf import FlaskForm
from json import dumps, loads
from json.decoder import JSONDecodeError
from ldap3 import Connection, NTLM, SUBTREE
from logging import info
from flask.wrappers import Response
from ipaddress import IPv4Network
from os import listdir
from pynetbox import api as netbox_api
from re import search, sub
from requests import get as http_get
from requests.exceptions import ConnectionError
from simplekml import Kml
from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError, DataError
from subprocess import Popen
from typing import Any, Dict, List, Union

from eNMS.controller import controller
from eNMS.modules import (
    bp,
    db,
    ldap_client,
    scheduler,
    tacacs_client,
    USE_LDAP,
    USE_TACACS,
)
from eNMS.forms import (
    form_classes,
    form_templates,
    AdministrationForm,
    DatabaseHelpersForm,
    LoginForm,
    MigrationsForm,
    CompareResultsForm,
    GoogleEarthForm,
    ImportExportForm,
    LibreNmsForm,
    NetboxForm,
    OpenNmsForm,
    WorkflowBuilderForm,
)
from eNMS.framework import (
    delete,
    delete_all,
    factory,
    fetch,
    fetch_all,
    fetch_all_visible,
    get,
    get_one,
    objectify,
    post,
    permission_required,
)
from eNMS.helpers import migrate_export, migrate_import, scheduler_job, str_dict
from eNMS.models import classes, service_classes
from eNMS.modules import bp
from eNMS.properties import (
    cls_to_properties,
    default_diagrams_properties,
    google_earth_styles,
    link_subtype_to_color,
    pretty_names,
    private_properties,
    property_types,
    reverse_pretty_names,
    subtype_sizes,
    table_fixed_columns,
    table_properties,
    type_to_diagram_properties,
)


@bp.route("/<endpoint>", methods=["GET"])
@login_required
def get_route(endpoint: str) -> Response:
    ctx = getattr(controller, endpoint)() or {}
    if not isinstance(ctx, dict):
        return ctx
    ctx["endpoint"] = endpoint
    info(
        f"User '{current_user.name}' ({request.remote_addr})"
        f"calling the endpoint {endpoint} (GET)"
    )
    return render_template(f"{ctx.pop('template', 'pages/' + endpoint)}.html", **ctx)


@bp.route("/<endpoint>", methods=["POST"])
@login_required
def post_route(endpoint: str) -> Response:
    data = {**request.form.to_dict(), **{"creator": current_user.id}}
    for property in data.get("list_fields", "").split(","):
        data[property] = request.form.getlist(property)
    for property in data.get("boolean_fields", "").split(","):
        data[property] = property in request.form
    request.form = data
    func, *args = endpoint.split("@")
    info(
        f"User '{current_user.name}' ({request.remote_addr})"
        f" calling the endpoint {request.url} (POST)"
    )
    try:
        result = getattr(controller, func)(*args)
        db.session.commit()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)})


@get("/filtering/<table>")
def filtering(table: str) -> Response:
    return jsonify(controller.filtering(table, request.args))


@get("/get_raw_logs/<int:device_id>/<version>", "Edit")
def get_raw_logs(device_id: int, version: str) -> str:
    device = fetch("Device", id=device_id)
    configurations = {str(k): v for k, v in device.configurations.items()}
    return f'<pre>{configurations.get(version, "")}</pre>'


@post("/get_git_content", "Admin")
def git_action() -> bool:
    parameters = get_one("Parameters")
    parameters.get_git_content(app)


@get("/import_export", "View")
def import_export() -> dict:
    return dict(
        import_export_form=ImportExportForm(request.form),
        librenms_form=LibreNmsForm(request.form),
        netbox_form=NetboxForm(request.form),
        opennms_form=OpenNmsForm(request.form),
        google_earth_form=GoogleEarthForm(request.form),
        parameters=get_one("Parameters"),
    )


@post("/import_topology", "Edit")
def import_topology() -> str:
    return controller.object_import(request.form, request.files["file"])


@bp.route("/login", methods=["GET", "POST"])
def login() -> Union[Response, str]:
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


@get("/logout")
def logout() -> Response:
    logout_user()
    return redirect(url_for("admin_blueprint.login"))


@post("/migration_<direction>", "Admin")
def migration(direction: str) -> Union[bool, str]:
    args = (app, request.form)
    return migrate_import(*args) if direction == "import" else migrate_export(*args)


@post("/reset_status", "Admin")
def reset_status() -> bool:
    for job in fetch_all("Job"):
        job.is_running = False


@get("/results/<int:id>/<runtime>", "View")
def results(id: int, runtime: str) -> str:
    job = fetch("Job", id=id)
    if not job:
        message = "The associated job has been deleted."
    else:
        message = job.results.get(runtime, "Results have been removed")
    return f"<pre>{dumps(message, indent=4)}</pre>"


@get("/<form_type>_form", "View")
def route_form(form_type: str) -> dict:
    return dict(
        form=form_classes.get(form_type, FlaskForm)(request.form),
        form_type=form_type,
        template=f"forms/{form_templates.get(form_type, form_type + '_form')}",
    )


@get("/<table_type>_management", "View")
def route_table(table_type: str) -> dict:
    return dict(
        properties=table_properties[table_type],
        fixed_columns=table_fixed_columns[table_type],
        type=table_type,
        template="pages/table",
    )


@post("/run_job/<int:job_id>", "Edit")
def run_job(job_id: int) -> dict:
    job = fetch("Job", id=job_id)
    if job.is_running:
        return {"error": "Job is already running."}
    targets = job.compute_targets()
    if hasattr(job, "has_targets"):
        if job.has_targets and not targets:
            return {"error": "Set devices or pools as targets first."}
        if not job.has_targets and targets:
            return {"error": "This service should not have targets configured."}
    scheduler.add_job(
        id=str(datetime.now()),
        func=scheduler_job,
        run_date=datetime.now(),
        args=[job.id],
        trigger="date",
    )
    return job.serialized


@post("/save_device_jobs/<int:device_id>", "Edit")
def save_device_jobs(device_id: int) -> bool:
    fetch("Device", id=device_id).jobs = objectify("Job", request.form["jobs"])


@post("/save_parameters", "Admin")
def save_parameters() -> bool:
    parameters = get_one("Parameters")
    parameters.update(**request.form)
    parameters.trigger_active_parameters(app)


@post("/save_pool_objects/<int:pool_id>", "Edit")
def save_pool_objects(pool_id: int) -> dict:
    pool = fetch("Pool", id=pool_id)
    pool.devices = objectify("Device", request.form["devices"])
    pool.links = objectify("Link", request.form["links"])
    return pool.serialized


@post("/save_positions/<int:workflow_id>", "Edit")
def save_positions(workflow_id: int) -> str:
    now = str(datetime.now())
    workflow = fetch("Workflow", id=workflow_id)
    workflow.last_modified = now
    session["workflow"] = workflow.id
    for job_id, position in request.json.items():
        job = fetch("Job", id=job_id)
        job.positions[workflow.name] = (position["x"], position["y"])
    return now


@post("/scan_cluster", "Admin")
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


@post("/scheduler/<action>", "Admin")
def scheduler_action(action: str) -> bool:
    getattr(scheduler, action)()


@bp.route("/")
def site_root() -> Response:
    return redirect(url_for("bp.login"))


@post("/<action>_task/<int:task_id>", "Edit")
def task_action(action: str, task_id: int) -> bool:
    getattr(fetch("Task", id=task_id), action)()


@post("/update/<cls>", "Edit")
def update_instance(cls: str) -> dict:
    try:
        instance = factory(cls, **request.form)
        info(f"{current_user.name}: UPDATE {cls} " f"{instance.name} ({instance.id})")
        return instance.serialized
    except JSONDecodeError:
        return {"error": "Invalid JSON syntax (JSON field)"}
    except IntegrityError:
        return {"error": "An object with the same name already exists"}


@post("/update_pool/<pool_id>", "Edit")
def update_pools(**kwargs) -> bool:
    controller.update_pools(**kwargs)


@get("/<view_type>_view", "View")
def view(view_type: str) -> dict:
    return dict(
        template="pages/geographical_view",
        parameters=get_one("Parameters").serialized,
        subtype_sizes=subtype_sizes,
        link_colors=link_subtype_to_color,
        view_type=view_type,
    )


@post("/view_filtering/<filter_type>")
def view_filtering(filter_type: str):
    model = filter_type.split("_")[0]
    model = classes[model]
    properties = table_properties[model] + ["current_configuration"]
    constraints = []
    for property in properties:
        value = request.form[property]
        if value:
            constraints.append(getattr(model, property).contains(value))
    result = db.session.query(model).filter(and_(*constraints))
    pools = [int(id) for id in request.args.getlist("form[pools][]")]
    if pools:
        result = result.filter(model.pools.any(classes["pool"].id.in_(pools)))
    return [d.get_properties() for d in result.all()]


@get("/workflow_builder", "View")
def workflow_builder() -> dict:
    workflow = fetch("Workflow", id=session.get("workflow", None))
    return dict(
        workflow=workflow.serialized if workflow else None,
        workflow_builder_form=WorkflowBuilderForm(request.form),
        compare_results_form=CompareResultsForm(request.form),
        services_classes=sorted(service_classes),
    )
