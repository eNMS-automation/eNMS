from datetime import datetime
from difflib import SequenceMatcher
from flask import current_app as app, jsonify, request, send_file
from flask.wrappers import Response
from flask_login import current_user
from pynetbox import api as netbox_api
from requests import get as http_get
from simplekml import Kml
from subprocess import Popen
from typing import Dict, List

from eNMS.extensions import db
from eNMS.functions import factory, fetch, fetch_all, get, get_one, objectify, post
from eNMS.inventory import bp
from eNMS.inventory.forms import (
    AddDevice,
    AddLink,
    AddPoolForm,
    CompareConfigurationsForm,
    DeviceAutomationForm,
    GoogleEarthForm,
    GottyConnectionForm,
    ImportExportForm,
    LibreNmsForm,
    NetboxForm,
    OpenNmsForm,
    PoolObjectsForm,
    PoolRestrictionForm,
)
from eNMS.inventory.functions import get_pools_devices, object_export, object_import
from eNMS.properties import (
    device_configuration_properties,
    device_table_properties,
    google_earth_styles,
    link_table_properties,
    pool_table_properties,
)


@get(bp, "/device_management", "View")
def device_management() -> dict:
    return dict(
        fields=device_table_properties,
        add_device_form=AddDevice(request.form),
        device_automation_form=DeviceAutomationForm(request.form),
        gotty_connection_form=GottyConnectionForm(request.form),
        pool_restriction_form=PoolRestrictionForm(request.form),
    )


@get(bp, "/configuration_management", "View")
def configuration_management() -> dict:
    return dict(
        add_device_form=AddDevice(request.form),
        fields=device_configuration_properties,
        compare_configurations_form=CompareConfigurationsForm(request.form),
        pool_restriction_form=PoolRestrictionForm(request.form),
    )


@get(bp, "/link_management", "View")
def link_management() -> dict:
    return dict(
        fields=link_table_properties,
        add_link_form=AddLink(request.form),
        pool_restriction_form=PoolRestrictionForm(request.form),
    )


@get(bp, "/pool_management", "View")
def pool_management() -> dict:
    return dict(
        add_pool_form=AddPoolForm(request.form),
        pool_object_form=PoolObjectsForm(request.form),
        fields=pool_table_properties,
        add_device_form=AddDevice(request.form),
        add_link_form=AddLink(request.form),
        device_automation_form=DeviceAutomationForm(request.form),
        gotty_connection_form=GottyConnectionForm(request.form),
    )


@get(bp, "/import_export", "View")
def import_export() -> dict:
    return dict(
        import_export_form=ImportExportForm(request.form),
        librenms_form=LibreNmsForm(request.form),
        netbox_form=NetboxForm(request.form),
        opennms_form=OpenNmsForm(request.form),
        google_earth_form=GoogleEarthForm(request.form),
        parameters=get_one("Parameters"),
    )


@get(bp, "/download_configuration/<name>", "View")
def download_configuration(name: str) -> Response:
    try:
        return send_file(
            filename_or_fp=str(app.path / "git" / "configurations" / name / name),
            as_attachment=True,
            attachment_filename=f"configuration_{name}.txt",
        )
    except FileNotFoundError:
        return jsonify("No configuration stored")


@post(bp, "/connection/<int:device_id>", "Connect to device")
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


@post(bp, "/save_device_jobs/<int:device_id>", "Edit")
def save_device_jobs(device_id: int) -> bool:
    fetch("Device", id=device_id).jobs = objectify("Job", request.form["jobs"])
    db.session.commit()
    return True


@post(bp, "/save_pool_objects/<int:pool_id>", "Edit")
def save_pool_objects(pool_id: int) -> dict:
    pool = fetch("Pool", id=pool_id)
    pool.devices = objectify("Device", request.form["devices"])
    pool.links = objectify("Link", request.form["links"])
    db.session.commit()
    return pool.serialized


@post(bp, "/pool_objects/<int:pool_id>", "View")
def filter_pool_objects(pool_id: int) -> Dict[str, List[dict]]:
    return get_pools_devices(pool_id)


@post(bp, "/pools_objects", "View")
def filter_pools_objects() -> Dict[str, List[dict]]:
    return get_pools_devices(*request.form["pools"])


@post(bp, "/update_pool/<pool_id>", "Edit")
def update_pools(pool_id: str) -> bool:
    if pool_id == "all":
        for pool in fetch_all("Pool"):
            pool.compute_pool()
    else:
        fetch("Pool", id=int(pool_id)).compute_pool()
    db.session.commit()
    return True


@post(bp, "/import_topology", "Edit")
def import_topology() -> str:
    return object_import(request.form, request.files["file"])


@post(bp, "/export_topology", "View")
def export_topology() -> bool:
    return object_export(request.form, app.path)


@post(bp, "/query_opennms", "Edit")
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


@post(bp, "/query_netbox", "Edit")
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


@post(bp, "/query_librenms", "Edit")
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


@post(bp, "/export_to_google_earth", "View")
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


@post(bp, "/get_configurations/<int:device_id>", "View")
def get_configurations(device_id: int) -> dict:
    return {str(k): v for k, v in fetch("Device", id=device_id).configurations.items()}


@post(bp, "/get_diff/<int:device_id>/<v1>/<v2>", "View")
def get_diff(device_id: int, v1: str, v2: str) -> dict:
    device = fetch("Device", id=device_id)
    d1, d2 = [datetime.strptime(d, "%Y-%m-%d %H:%M:%S.%f") for d in (v1, v2)]
    first = device.configurations[d1].splitlines()
    second = device.configurations[d2].splitlines()
    opcodes = SequenceMatcher(None, first, second).get_opcodes()
    return {"first": first, "second": second, "opcodes": opcodes}


@post(bp, "/clear_configurations/<int:device_id>", "Edit")
def clear_configurations(device_id: int) -> bool:
    fetch("Device", id=device_id).configurations = {}
    db.session.commit()
    return True


@get(bp, "/get_raw_logs/<int:device_id>/<version>", "Edit")
def get_raw_logs(device_id: int, version: str) -> str:
    device = fetch("Device", id=device_id)
    configurations = {str(k): v for k, v in device.configurations.items()}
    return f'<pre>{configurations.get(version, "")}</pre>'
