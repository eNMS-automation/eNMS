from collections import Counter
from datetime import datetime
from difflib import SequenceMatcher
from flask_wtf import FlaskForm
from json.decoder import JSONDecodeError
from logging import info
from flask import current_app as app, jsonify, redirect, request, send_file, url_for
from flask.wrappers import Response
from flask_login import current_user
from pynetbox import api as netbox_api
from requests import get as http_get
from simplekml import Kml
from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError
from subprocess import Popen
from typing import Dict, List, Union
from werkzeug.wrappers import Response

from eNMS import db
from eNMS.classes import classes
from eNMS.extensions import bp
from eNMS.forms import (
    form_classes,
    form_templates,
    GoogleEarthForm,
    ImportExportForm,
    LibreNmsForm,
    NetboxForm,
    OpenNmsForm,
)
from eNMS.functions import (
    delete,
    factory,
    fetch,
    fetch_all,
    fetch_all_visible,
    get,
    get_one,
    objectify,
    post,
)
from eNMS.inventory.functions import object_export, object_import
from eNMS.properties import (
    default_diagrams_properties,
    google_earth_styles,
    link_subtype_to_color,
    reverse_pretty_names,
    subtype_sizes,
    table_fixed_columns,
    table_properties,
    type_to_diagram_properties,
)


@bp.route("/")
def site_root() -> Response:
    return redirect(url_for("bp.login"))


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


@get("/<view_type>_view", "View")
def view(view_type: str) -> dict:
    return dict(
        template="pages/geographical_view",
        parameters=get_one("Parameters").serialized,
        subtype_sizes=subtype_sizes,
        link_colors=link_subtype_to_color,
        view_type=view_type,
    )


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


@get("/filtering/<table>")
def filtering(table: str) -> Response:
    model = classes.get(table, classes["Device"])
    properties = table_properties[table]
    if table in ("configuration", "device"):
        properties.append("current_configuration")
    try:
        order_property = properties[int(request.args["order[0][column]"])]
    except IndexError:
        order_property = "name"
    order = getattr(getattr(model, order_property), request.args["order[0][dir]"])()
    constraints = []
    for property in properties:
        value = request.args.get(f"form[{property}]")
        if value:
            constraints.append(getattr(model, property).contains(value))
    result = db.session.query(model).filter(and_(*constraints)).order_by(order)
    if table in ("device", "link", "configuration"):
        pools = [int(id) for id in request.args.getlist("form[pools][]")]
        if pools:
            result = result.filter(model.pools.any(classes["pool"].id.in_(pools)))
    return jsonify(
        {
            "draw": int(request.args["draw"]),
            "recordsTotal": len(model.query.all()),
            "recordsFiltered": len(result.all()),
            "data": [
                [getattr(obj, property) for property in properties]
                + obj.generate_row(table)
                for obj in result.limit(int(request.args["length"]))
                .offset(int(request.args["start"]))
                .all()
            ],
        }
    )


@post("/view_filtering/<filter_type>")
def view_filtering(filter_type: str):
    print(request.form)
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


@post("/get_logs/<int:device_id>", "View")
def get_logs(device_id: int) -> Union[str, bool]:
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


@post("/get_all/<cls>", "View")
def get_all_instances(cls: str) -> List[dict]:
    info(f"{current_user.name}: GET ALL {cls}")
    return [instance.get_properties() for instance in fetch_all_visible(cls)]


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


@post("/delete/<cls>/<id>", "Edit")
def delete_instance(cls: str, id: str) -> dict:
    instance = delete(cls, id=id)
    info(f'{current_user.name}: DELETE {cls} {instance["name"]} ({id})')
    return instance


@post("/counters/<property>/<type>")
def get_counters(property: str, type: str) -> Counter:
    objects = fetch_all(type)
    if property in reverse_pretty_names:
        property = reverse_pretty_names[property]
    return Counter(map(lambda o: str(getattr(o, property)), objects))


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


@post("/save_device_jobs/<int:device_id>", "Edit")
def save_device_jobs(device_id: int) -> bool:
    fetch("Device", id=device_id).jobs = objectify("Job", request.form["jobs"])
    db.session.commit()
    return True


@post("/save_pool_objects/<int:pool_id>", "Edit")
def save_pool_objects(pool_id: int) -> dict:
    pool = fetch("Pool", id=pool_id)
    pool.devices = objectify("Device", request.form["devices"])
    pool.links = objectify("Link", request.form["links"])
    db.session.commit()
    return pool.serialized


@post("/update_pool/<pool_id>", "Edit")
def update_pools(pool_id: str) -> bool:
    if pool_id == "all":
        for pool in fetch_all("Pool"):
            pool.compute_pool()
    else:
        fetch("Pool", id=int(pool_id)).compute_pool()
    db.session.commit()
    return True


@post("/import_topology", "Edit")
def import_topology() -> str:
    return object_import(request.form, request.files["file"])


@post("/export_topology", "View")
def export_topology() -> bool:
    return object_export(request.form, app.path)


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


@post("/get_configurations/<int:device_id>", "View")
def get_configurations(device_id: int) -> dict:
    return {str(k): v for k, v in fetch("Device", id=device_id).configurations.items()}


@post("/get_diff/<int:device_id>/<v1>/<v2>", "View")
def get_diff(device_id: int, v1: str, v2: str) -> dict:
    device = fetch("Device", id=device_id)
    d1, d2 = [datetime.strptime(d, "%Y-%m-%d %H:%M:%S.%f") for d in (v1, v2)]
    first = device.configurations[d1].splitlines()
    second = device.configurations[d2].splitlines()
    opcodes = SequenceMatcher(None, first, second).get_opcodes()
    return {"first": first, "second": second, "opcodes": opcodes}


@post("/clear_configurations/<int:device_id>", "Edit")
def clear_configurations(device_id: int) -> bool:
    fetch("Device", id=device_id).configurations = {}
    db.session.commit()
    return True


@get("/get_raw_logs/<int:device_id>/<version>", "Edit")
def get_raw_logs(device_id: int, version: str) -> str:
    device = fetch("Device", id=device_id)
    configurations = {str(k): v for k, v in device.configurations.items()}
    return f'<pre>{configurations.get(version, "")}</pre>'


@post("/shutdown", "Admin")
def shutdown() -> str:
    info(f"{current_user.name}: SHUTDOWN eNMS")
    func = request.environ.get("werkzeug.server.shutdown")
    if func is None:
        raise RuntimeError("Not running with the Werkzeug Server")
    func()
    return "Server shutting down..."
