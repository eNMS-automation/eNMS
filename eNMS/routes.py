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
)
from eNMS.helpers import (
    migrate_export,
    migrate_import,
    object_export,
    object_import,
    scheduler_job,
    str_dict,
)
from eNMS.models import classes, service_classes
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


@post("/add_edge/<int:workflow_id>/<subtype>/<int:source>/<int:dest>", "Edit")
def add_edge(workflow_id: int, subtype: str, source: int, dest: int) -> dict:
    workflow_edge = factory(
        "WorkflowEdge",
        **{
            "name": f"{workflow_id}-{subtype}:{source}->{dest}",
            "workflow": workflow_id,
            "subtype": subtype,
            "source": source,
            "destination": dest,
        },
    )
    now = str(datetime.now())
    fetch("Workflow", id=workflow_id).last_modified = now
    db.session.commit()
    return {"edge": workflow_edge.serialized, "update_time": now}


@post("/add_jobs_to_workflow/<int:workflow_id>", "Edit")
def add_jobs_to_workflow(workflow_id: int) -> Dict[str, Any]:
    workflow = fetch("Workflow", id=workflow_id)
    jobs = objectify("Job", request.form["add_jobs"])
    for job in jobs:
        job.workflows.append(workflow)
    now = str(datetime.now())
    workflow.last_modified = now
    db.session.commit()
    return {"jobs": [job.serialized for job in jobs], "update_time": now}


@get("/administration", "View")
def administration() -> dict:
    return dict(
        form=AdministrationForm(request.form),
        parameters=get_one("Parameters").serialized,
    )


@get("/advanced", "View")
def advanced() -> dict:
    return dict(
        database_helpers_form=DatabaseHelpersForm(request.form),
        migrations_form=MigrationsForm(request.form),
        folders=listdir(app.path / "migrations"),
    )


@get("/calendar", "View")
def calendar() -> dict:
    tasks = {}
    for task in fetch_all("Task"):
        # javascript dates range from 0 to 11, we must account for that by
        # substracting 1 to the month for the date to be properly displayed in
        # the calendar
        date = task.next_run_time
        if not date:
            continue
        python_month = search(r".*-(\d{2})-.*", date).group(1)  # type: ignore
        month = "{:02}".format((int(python_month) - 1) % 12)
        js_date = [
            int(i)
            for i in sub(
                r"(\d+)-(\d+)-(\d+) (\d+):(\d+).*", r"\1," + month + r",\3,\4,\5", date
            ).split(",")
        ]
        tasks[task.name] = {**task.serialized, **{"date": js_date}}
    return dict(tasks=tasks)


@post("/clear_configurations/<int:device_id>", "Edit")
def clear_configurations(device_id: int) -> bool:
    fetch("Device", id=device_id).configurations = {}
    return True


@post("/clear_results/<int:job_id>", "Edit")
def clear_results(job_id: int) -> bool:
    fetch("Job", id=job_id).results = {}
    return True


@post("/connection/<int:device_id>", "Connect to device")
def connection(device_id: int) -> dict:
    parameters, device = get_one("Parameters"), fetch("Device", id=device_id)
    cmd = [str(app.path / "applications" / "gotty"), "-w"]
    port, protocol = parameters.get_gotty_port(), request.form["protocol"]
    address = getattr(device, request.form["address"])
    cmd.extend(["-p", str(port)])
    if "accept-once" in request.form:
        cmd.append("--once")
    if "multiplexing" in request.form:
        cmd.extend(f"tmux new -A -s gotty{port}".split())
    if app.config["GOTTY_BYPASS_KEY_PROMPT"]:
        options = "-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"
    else:
        options = ""
    if protocol == "telnet":
        cmd.extend(f"telnet {address}".split())
    elif "authentication" in request.form:
        if request.form["credentials"] == "device":
            login, pwd = device.username, device.password
        else:
            login, pwd = current_user.name, current_user.password
        cmd.extend(f"sshpass -p {pwd} ssh {options} {login}@{address}".split())
    else:
        cmd.extend(f"ssh {options} {address}".split())
    if protocol != "telnet":
        cmd.extend(f"-p {device.port}".split())
    Popen(cmd)
    return {
        "device": device.name,
        "port": port,
        "redirection": app.config["GOTTY_PORT_REDIRECTION"],
        "server_addr": app.config["ENMS_SERVER_ADDR"],
    }


@get("/dashboard")
def dashboard() -> dict:
    on_going = {
        "Running services": len(
            [service for service in fetch_all("Service") if service.status == "Running"]
        ),
        "Running workflows": len(
            [
                workflow
                for workflow in fetch_all("Workflow")
                if workflow.status == "Running"
            ]
        ),
        "Scheduled tasks": len(
            [task for task in fetch_all("Task") if task.status == "Active"]
        ),
    }
    return dict(
        properties=type_to_diagram_properties,
        default_properties=default_diagrams_properties,
        counters={**{cls: len(fetch_all_visible(cls)) for cls in classes}, **on_going},
    )


@post("/database_helpers", "Admin")
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
    return True


@post("/delete_edge/<int:workflow_id>/<int:edge_id>", "Edit")
def delete_edge(workflow_id: int, edge_id: int) -> str:
    delete("WorkflowEdge", id=edge_id)
    now = str(datetime.now())
    fetch("Workflow", id=workflow_id).last_modified = now
    return now


@post("/delete/<cls>/<int:instance_id>", "Edit")
def delete_instance(cls: str, instance_id: int) -> dict:
    return controller.delete_instance(cls, instance_id)


@post("/delete_node/<int:workflow_id>/<int:job_id>", "Edit")
def delete_node(workflow_id: int, job_id: int) -> dict:
    workflow, job = fetch("Workflow", id=workflow_id), fetch("Job", id=job_id)
    workflow.jobs.remove(job)
    now = str(datetime.now())
    workflow.last_modified = now
    return {"job": job.serialized, "update_time": now}


@get("/download_configuration/<name>", "View")
def download_configuration(name: str) -> Response:
    try:
        return send_file(
            filename_or_fp=str(app.path / "git" / "configurations" / name / name),
            as_attachment=True,
            attachment_filename=f"configuration_{name}.txt",
        )
    except FileNotFoundError:
        return jsonify("No configuration stored")


@post("/duplicate_workflow/<int:workflow_id>", "Edit")
def duplicate_workflow(workflow_id: int) -> dict:
    parent_workflow = fetch("Workflow", id=workflow_id)
    new_workflow = factory("Workflow", **request.form)
    for job in parent_workflow.jobs:
        new_workflow.jobs.append(job)
        job.positions[new_workflow.name] = job.positions[parent_workflow.name]
    for edge in parent_workflow.edges:
        subtype, src, destination = edge.subtype, edge.source, edge.destination
        new_workflow.edges.append(
            factory(
                "WorkflowEdge",
                **{
                    "name": f"{new_workflow.id}-{subtype}:{src.id}->{destination.id}",
                    "workflow": new_workflow.id,
                    "subtype": subtype,
                    "source": src.id,
                    "destination": destination.id,
                },
            )
        )
    db.session.commit()
    return new_workflow.serialized


@post("/export_to_google_earth", "View")
def export_to_google_earth() -> bool:
    kml_file = Kml()
    for device in fetch_all("Device"):
        point = kml_file.newpoint(name=device.name)
        point.coords = [(device.longitude, device.latitude)]
        point.style = google_earth_styles[device.subtype]
        point.style.labelstyle.scale = request.form["label_size"]
    for link in fetch_all("Link"):
        line = kml_file.newlinestring(name=link.name)
        line.coords = [
            (link.source.longitude, link.source.latitude),
            (link.destination.longitude, link.destination.latitude),
        ]
        line.style = google_earth_styles[link.subtype]
        line.style.linestyle.width = request.form["line_width"]
    filepath = app.path / "google_earth" / f'{request.form["name"]}.kmz'
    kml_file.save(filepath)
    return True


@post("/export_topology", "View")
def export_topology() -> bool:
    return object_export(request.form, app.path)


@get("/filtering/<table>")
def filtering(table: str) -> Response:
    return jsonify(controller.filtering(table, request.args))


@post("/get_all/<cls>", "View")
def get_all_instances(cls: str) -> List[dict]:
    info(f"{current_user.name}: GET ALL {cls}")
    return [instance.get_properties() for instance in fetch_all_visible(cls)]


@post("/get_cluster_status", "View")
def get_cluster_status() -> dict:
    return controller.get_cluster_status()


@post("/get_configurations/<int:device_id>", "View")
def get_configurations(device_id: int) -> dict:
    return fetch("Device", id=device_id).get_configurations()


@post("/get_configuration_diff/<int:device_id>/<v1>/<v2>", "View")
def get_configuration_diff(device_id: int, v1: str, v2: str) -> dict:
    device = fetch("Device", id=device_id)
    d1, d2 = [datetime.strptime(d, "%Y-%m-%d %H:%M:%S.%f") for d in (v1, v2)]
    first = device.configurations[d1].splitlines()
    second = device.configurations[d2].splitlines()
    opcodes = SequenceMatcher(None, first, second).get_opcodes()
    return {"first": first, "second": second, "opcodes": opcodes}


@post("/counters/<property>/<type>")
def get_counters(property: str, type: str) -> Counter:
    return controller.get_counters(property, type)


@post("/get_device_logs/<int:device_id>", "View")
def get_device_logs(device_id: int) -> Union[str, bool]:
    device_logs = [
        log.content
        for log in fetch_all("Log")
        if log.source == fetch("Device", id=device_id).ip_address
    ]
    return "\n".join(device_logs) or True


@post("/get/<cls>/<id>", "View")
def get_instance(cls: str, id: str) -> dict:
    instance = fetch(cls, id=id)
    info(f"{current_user.name}: GET {cls} {instance.name} ({id})")
    return instance.serialized


@post("/get_job_logs/<int:id>", "View")
def get_job_logs(id: int) -> dict:
    job = fetch("Job", id=id)
    return {"logs": job.logs, "running": job.is_running}


@get("/get_raw_logs/<int:device_id>/<version>", "Edit")
def get_raw_logs(device_id: int, version: str) -> str:
    device = fetch("Device", id=device_id)
    configurations = {str(k): v for k, v in device.configurations.items()}
    return f'<pre>{configurations.get(version, "")}</pre>'


@post("/get_results/<int:id>", "View")
def get_results(id: int) -> dict:
    return fetch("Job", id=id).results


@post("/get_results_diff/<int:job_id>/<v1>/<v2>", "View")
def get_results_diff(job_id: int, v1: str, v2: str) -> dict:
    job = fetch("Job", id=job_id)
    first = str_dict(dict(reversed(sorted(job.results[v1].items())))).splitlines()
    second = str_dict(dict(reversed(sorted(job.results[v2].items())))).splitlines()
    opcodes = SequenceMatcher(None, first, second).get_opcodes()
    return {"first": first, "second": second, "opcodes": opcodes}


@post("/get_service/<id_or_cls>", "View")
def get_service(id_or_cls: str) -> dict:
    service = None
    try:
        service = fetch("Service", id=id_or_cls)
    except DataError:
        pass
    cls = service_classes[service.type if service else id_or_cls]
    pre_id = f"{service.id}-" if service else ""

    def build_text_box(property: str, name: str) -> str:
        return f"""
            <label>{name}</label>
            <div class="form-group">
              <input
                class="form-control"
                id="{pre_id}service-{property}"
                maxlength="{getattr(cls, f'{property}_length', 524288)}"
                name="{property}"
                type="{'password' if property in private_properties else 'text'}"
              >
            </div>"""

    def build_textarea_box(property: str, name: str) -> str:
        return f"""
            <label>{name}</label>
            <div class="form-group">
              <textarea
                style="height: 150px;" rows="30"
                maxlength="{getattr(cls, f'{property}_length', 524288)}"
                class="form-control"
                id="{pre_id}service-{property}"
                name="{property}"
              ></textarea>
            </div>"""

    def build_select_box(property: str, name: str) -> str:
        options = "".join(
            f'<option value="{k}">{v}</option>'
            for k, v in getattr(cls, f"{property}_values")
        )
        return f"""
            <label>{name}</label>
            <div class="form-group">
              <select
                class="form-control"
                id="{pre_id}service-{property}"
                name="{property}"
                {'multiple size="7"' if property_types[property] == 'list' else ''}
              >
              {options}
              </select>
            </div>"""

    def build_boolean_box(property: str, name: str) -> str:
        return (
            "<fieldset>"
            + f"""
            <div class="item">
              <input
                id="{pre_id}service-{property}"
                name="{property}"
                type="checkbox"
              >
              <label>{name}</label>
            </div>"""
            + "</fieldset>"
        )

    form, list_properties, boolean_properties = "", [], []
    for property in cls_to_properties[cls.__tablename__]:
        name = getattr(cls, f"{property}_name", pretty_names.get(property, property))
        if property in cls_to_properties["Service"]:
            continue
        if property_types.get(property, None) == "bool":
            form += build_boolean_box(property, name)
            boolean_properties.append(property)
        elif hasattr(cls, f"{property}_values"):
            form += build_select_box(property, name)
            if property_types[property] == "list":
                list_properties.append(property)
        elif hasattr(cls, f"{property}_textarea"):
            form += build_textarea_box(property, name)
        else:
            form += build_text_box(property, name)
    return {
        "boolean_properties": ",".join(boolean_properties),
        "html": form,
        "list_properties": ",".join(list_properties),
        "service": service.serialized if service else None,
    }


@post("/get_git_content", "Admin")
def git_action() -> bool:
    parameters = get_one("Parameters")
    parameters.get_git_content(app)
    return True


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
    return object_import(request.form, request.files["file"])


@bp.route("/login", methods=["GET", "POST"])
def login() -> Union[Response, str]:
    if request.method == "POST":
        name, password = request.form["name"], request.form["password"]
        try:
            if request.form["authentication_method"] == "Local User":
                user = fetch("User", name=name)
                if user and password == user.password:
                    login_user(user)
                    return redirect(url_for("bp.dashboard"))
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
                        return redirect(url_for("bp.dashboard"))
            elif request.form["authentication_method"] == "TACACS":
                if tacacs_client.authenticate(name, password).valid:
                    user = factory("User", **{"name": name, "password": password})
                    login_user(user)
                    return redirect(url_for("bp.dashboard"))
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
    return redirect(url_for("bp.dashboard"))


@get("/logout")
def logout() -> Response:
    logout_user()
    return redirect(url_for("admin_blueprint.login"))


@post("/migration_<direction>", "Admin")
def migration(direction: str) -> Union[bool, str]:
    args = (app, request.form)
    return migrate_import(*args) if direction == "import" else migrate_export(*args)


@post("/query_netbox", "Edit")
def query_netbox() -> bool:
    nb = netbox_api(request.form["netbox_address"], token=request.form["netbox_token"])
    for device in nb.dcim.devices.all():
        device_ip = device.primary_ip4 or device.primary_ip6
        factory(
            "Device",
            **{
                "name": device.name,
                "ip_address": str(device_ip).split("/")[0],
                "subtype": request.form["netbox_type"],
                "longitude": 0.0,
                "latitude": 0.0,
            },
        )
    return True


@post("/query_librenms", "Edit")
def query_librenms() -> bool:
    devices = http_get(
        f'{request.form["librenms_address"]}/api/v0/devices',
        headers={"X-Auth-Token": request.form["librenms_token"]},
    ).json()["devices"]
    for device in devices:
        factory(
            "Device",
            **{
                "name": device["hostname"],
                "ip_address": device["ip"] or device["hostname"],
                "subtype": request.form["librenms_type"],
                "longitude": 0.0,
                "latitude": 0.0,
            },
        )
    db.session.commit()
    return True


@post("/query_opennms", "Edit")
def query_opennms() -> bool:
    parameters = get_one("Parameters")
    login, password = parameters.opennms_login, request.form["password"]
    parameters.update(**request.form)
    db.session.commit()
    json_devices = http_get(
        parameters.opennms_devices,
        headers={"Accept": "application/json"},
        auth=(login, password),
    ).json()["node"]
    devices = {
        device["id"]: {
            "name": device.get("label", device["id"]),
            "description": device["assetRecord"].get("description", ""),
            "location": device["assetRecord"].get("building", ""),
            "vendor": device["assetRecord"].get("manufacturer", ""),
            "model": device["assetRecord"].get("modelNumber", ""),
            "operating_system": device.get("operatingSystem", ""),
            "os_version": device["assetRecord"].get("sysDescription", ""),
            "longitude": device["assetRecord"].get("longitude", 0.0),
            "latitude": device["assetRecord"].get("latitude", 0.0),
            "subtype": request.form["subtype"],
        }
        for device in json_devices
    }
    for device in list(devices):
        link = http_get(
            f"{parameters.opennms_rest_api}/nodes/{device}/ipinterfaces",
            headers={"Accept": "application/json"},
            auth=(login, password),
        ).json()
        for interface in link["ipInterface"]:
            if interface["snmpPrimary"] == "P":
                devices[device]["ip_address"] = interface["ipAddress"]
                factory("Device", **devices[device])
    db.session.commit()
    return True


@post("/reset_status", "Admin")
def reset_status() -> bool:
    for job in fetch_all("Job"):
        job.is_running = False
    db.session.commit()
    return True


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
    db.session.commit()
    return True


@post("/save_parameters", "Admin")
def save_parameters() -> bool:
    parameters = get_one("Parameters")
    parameters.update(**request.form)
    parameters.trigger_active_parameters(app)
    db.session.commit()
    return True


@post("/save_pool_objects/<int:pool_id>", "Edit")
def save_pool_objects(pool_id: int) -> dict:
    pool = fetch("Pool", id=pool_id)
    pool.devices = objectify("Device", request.form["devices"])
    pool.links = objectify("Link", request.form["links"])
    db.session.commit()
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
    db.session.commit()
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
    db.session.commit()
    return True


@post("/scheduler/<action>", "Admin")
def scheduler_action(action: str) -> bool:
    getattr(scheduler, action)()
    return True


@bp.route("/")
def site_root() -> Response:
    return redirect(url_for("bp.login"))


@post("/<action>_task/<int:task_id>", "Edit")
def task_action(action: str, task_id: int) -> bool:
    getattr(fetch("Task", id=task_id), action)()
    return True


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
def update_pools(pool_id: str) -> bool:
    if pool_id == "all":
        for pool in fetch_all("Pool"):
            pool.compute_pool()
    else:
        fetch("Pool", id=int(pool_id)).compute_pool()
    db.session.commit()
    return True


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
