from collections import Counter
from copy import deepcopy
from flask import current_app, request
from logging import info
from os import makedirs
from os.path import exists
from pynetbox import api as netbox_api
from requests import get as http_get
from simplekml import Kml
from typing import Set
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename
from xlrd import open_workbook
from xlrd.biffh import XLRDError
from xlwt import Workbook
from yaml import dump, load, BaseLoader

from eNMS.default import create_default
from eNMS.forms import (
    GoogleEarthForm,
    ImportExportForm,
    LibreNmsForm,
    NetboxForm,
    OpenNmsForm,
)
from eNMS.framework import delete_all, export, factory, fetch_all, get_one
from eNMS.modules import db
from eNMS.properties import google_earth_styles, reverse_pretty_names
from eNMS.properties import export_properties


class ImportExportController:
    def export_to_google_earth(self) -> None:
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
        filepath = current_app.path / "google_earth" / f'{request.form["name"]}.kmz'
        kml_file.save(filepath)

    def get_cluster_status(self) -> dict:
        return {
            attr: [getattr(instance, attr) for instance in fetch_all("Instance")]
            for attr in ("status", "cpu_load")
        }

    def get_counters(self, property: str, type: str) -> Counter:
        property = reverse_pretty_names.get(property, property)
        return Counter(str(getattr(instance, property)) for instance in fetch_all(type))

    def allowed_file(self, name: str, allowed_modules: Set[str]) -> bool:
        allowed_syntax = "." in name
        allowed_extension = name.rsplit(".", 1)[1].lower() in allowed_modules
        return allowed_syntax and allowed_extension

    def object_import(self, request: dict, file: FileStorage) -> str:
        if request["replace"]:
            delete_all("Device")
        result = "Topology successfully imported."
        if self.allowed_file(secure_filename(file.filename), {"xls", "xlsx"}):
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

    def export_topology(self) -> None:
        workbook = Workbook()
        filename = request.form["export_filename"]
        if "." not in filename:
            filename += ".xls"
        for obj_type in ("Device", "Link"):
            sheet = workbook.add_sheet(obj_type)
            for index, property in enumerate(export_properties[obj_type]):
                sheet.write(0, index, property)
                for obj_index, obj in enumerate(fetch_all(obj_type), 1):
                    sheet.write(obj_index, index, getattr(obj, property))
        workbook.save(current_app.path / "projects" / filename)

    def import_export(self) -> dict:
        return dict(
            import_export_form=ImportExportForm(request.form),
            librenms_form=LibreNmsForm(request.form),
            netbox_form=NetboxForm(request.form),
            opennms_form=OpenNmsForm(request.form),
            google_earth_form=GoogleEarthForm(request.form),
            parameters=get_one("Parameters"),
        )

    def import_from_netbox(self) -> None:
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

    def import_from_librenms(self) -> None:
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

    def import_from_opennms(self):
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

    def migrate_export(self) -> None:
        for cls_name in request.form["import_export_types"]:
            path = current_app.path / "migrations" / request.form["name"]
            if not exists(path):
                makedirs(path)
            with open(path / f"{cls_name}.yaml", "w") as migration_file:
                dump(export(cls_name), migration_file, default_flow_style=False)

    def migrate_import(self) -> str:
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
        print("fix")
        if request.form.get("empty_database_before_import", False):
            create_default(current_app)
        return status
