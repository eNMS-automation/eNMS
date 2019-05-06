from collections import Counter
from datetime import datetime
from difflib import SequenceMatcher
from flask import current_app, request
from flask_login import current_user
from logging import info
from pynetbox import api as netbox_api
from requests import get as http_get
from simplekml import Kml
from sqlalchemy import and_
from subprocess import Popen
from typing import Union
from werkzeug.utils import secure_filename
from xlrd import open_workbook
from xlrd.biffh import XLRDError
from xlwt import Workbook

from eNMS.controller import controller
from eNMS.database_helpers import (
    delete_all,
    factory,
    fetch,
    fetch_all,
    fetch_all_visible,
    get_one,
    objectify,
)
from eNMS.models import classes
from eNMS.properties import (
    filtering_properties,
    table_properties,
    type_to_diagram_properties,
)


class InventoryDispatcher:
    def clear_configurations(self, device_id: int) -> None:
        fetch("Device", id=device_id).configurations = {}

    def connection(self, device_id: int) -> dict:
        parameters, device = get_one("Parameters"), fetch("Device", id=device_id)
        cmd = [str(current_app.path / "applications" / "gotty"), "-w"]
        port, protocol = parameters.get_gotty_port(), request.form["protocol"]
        address = getattr(device, request.form["address"])
        cmd.extend(["-p", str(port)])
        if "accept-once" in request.form:
            cmd.append("--once")
        if "multiplexing" in request.form:
            cmd.extend(f"tmux new -A -s gotty{port}".split())
        if controller.config["GOTTY_BYPASS_KEY_PROMPT"]:
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
            "redirection": controller.config["GOTTY_PORT_REDIRECTION"],
            "server_addr": controller.config["ENMS_SERVER_ADDR"],
        }

    def counters(self, property: str, type: str) -> Counter:
        return Counter(str(getattr(instance, property)) for instance in fetch_all(type))

    def dashboard(self) -> dict:
        return dict(
            properties=type_to_diagram_properties,
            counters={
                **{cls: len(fetch_all_visible(cls)) for cls in classes},
                **{
                    "Running services": len(
                        [
                            service
                            for service in fetch_all("Service")
                            if service.status == "Running"
                        ]
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
                },
            },
        )

    def export_topology(self) -> None:
        workbook = Workbook()
        filename = request.form["export_filename"]
        if "." not in filename:
            filename += ".xls"
        for obj_type in ("Device", "Link"):
            sheet = workbook.add_sheet(obj_type)
            for index, property in enumerate(table_properties[obj_type]):
                sheet.write(0, index, property)
                for obj_index, obj in enumerate(fetch_all(obj_type), 1):
                    sheet.write(obj_index, index, getattr(obj, property))
        workbook.save(current_app.path / "projects" / filename)

    def export_to_google_earth(self) -> None:
        kml_file = Kml()
        for device in fetch_all("Device"):
            point = kml_file.newpoint(name=device.name)
            point.coords = [(device.longitude, device.latitude)]
            point.style = controller.google_earth_styles[device.subtype]
            point.style.labelstyle.scale = request.form["label_size"]
        for link in fetch_all("Link"):
            line = kml_file.newlinestring(name=link.name)
            line.coords = [
                (link.source.longitude, link.source.latitude),
                (link.destination.longitude, link.destination.latitude),
            ]
            line.style = controller.google_earth_styles[link.subtype]
            line.style.linestyle.width = request.form["line_width"]
        filepath = current_app.path / "google_earth" / f'{request.form["name"]}.kmz'
        kml_file.save(filepath)

    def get_configurations(self, device_id: int) -> dict:
        return fetch("Device", id=device_id).get_configurations()

    def get_configuration_diff(self, device_id: int, v1: str, v2: str) -> dict:
        device = fetch("Device", id=device_id)
        d1, d2 = [datetime.strptime(d, "%Y+%m+%d %H:%M:%S.%f") for d in (v1, v2)]
        first = device.configurations[d1].splitlines()
        second = device.configurations[d2].splitlines()
        opcodes = SequenceMatcher(None, first, second).get_opcodes()
        return {"first": first, "second": second, "opcodes": opcodes}

    def get_device_logs(self, device_id: int) -> Union[str, bool]:
        device_logs = [
            log.content
            for log in fetch_all("Log")
            if log.source == fetch("Device", id=device_id).ip_address
        ]
        return "\n".join(device_logs)

    def query_netbox(self) -> None:
        nb = netbox_api(
            request.form["netbox_address"], token=request.form["netbox_token"]
        )
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

    def query_librenms(self) -> None:
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

    def query_opennms(self):
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

    def import_topology(self) -> str:
        file = request.files["file"]
        if request.form["replace"]:
            delete_all("Device")
        result = "Topology successfully imported."
        if controller.allowed_file(secure_filename(file.filename), {"xls", "xlsx"}):
            book = open_workbook(file_contents=file.read())
            for obj_type in ("Device", "Link"):
                try:
                    sheet = book.sheet_by_name(obj_type)
                except XLRDError:
                    continue
                properties = sheet.row_values(0)
                for row_index in range(1, sheet.nrows):
                    values = dict(zip(properties, sheet.row_values(row_index)))
                    values["dont_update_pools"] = True
                    try:
                        factory(obj_type, **values).serialized
                    except Exception as e:
                        info(f"{str(values)} could not be imported ({str(e)})")
                        result = "Partial import (see logs)."
                db.session.commit()
        for pool in fetch_all("Pool"):
            pool.compute_pool()
        db.session.commit()
        info("Inventory import: Done.")
        return result

    def save_pool_objects(self, pool_id: int) -> dict:
        pool = fetch("Pool", id=pool_id)
        pool.devices = objectify("Device", request.form["devices"])
        pool.links = objectify("Link", request.form["links"])
        return pool.serialized

    def update_pools(self, pool_id: str) -> None:
        if pool_id == "all":
            for pool in fetch_all("Pool"):
                pool.compute_pool()
        else:
            fetch("Pool", id=int(pool_id)).compute_pool()

    def view(self, view_type: str) -> dict:
        return dict(
            template="pages/view",
            link_colors=controller.link_colors,
            view_type=view_type,
        )

    def get_view_topology(self) -> dict:
        return {
            "devices": [d.view_properties for d in fetch_all("Device")],
            "links": [d.view_properties for d in fetch_all("Link")],
        }

    def view_filtering(self, filter_type: str):
        obj_type = filter_type.split("_")[0]
        model = classes[obj_type]
        constraints = []
        for property in filtering_properties[obj_type]:
            value = request.form[property]
            if value:
                constraints.append(getattr(model, property).contains(value))
        result = db.session.query(model).filter(and_(*constraints))
        pools = [int(id) for id in request.form["pools"]]
        if pools:
            result = result.filter(model.pools.any(classes["pool"].id.in_(pools)))
        return [d.view_properties for d in result.all()]
