from collections import Counter
from contextlib import contextmanager
from flask import Flask
from flask.wrappers import Response
from flask_login import current_user
from logging import info
from pathlib import Path, PosixPath
from sqlalchemy import and_
from sqlalchemy.orm import Session
from typing import Generator, Set
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename
from xlrd import open_workbook
from xlrd.biffh import XLRDError
from xlwt import Workbook

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
from eNMS.models import classes, service_classes
from eNMS.modules import (
    bp,
    db,
    ldap_client,
    scheduler,
    tacacs_client,
    USE_LDAP,
    USE_TACACS,
)
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


class ImportExportController:
    def export_to_google_earth() -> None:
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

    def object_export(self, request: dict, path_app: PosixPath) -> None:
        workbook = Workbook()
        filename = request["export_filename"]
        if "." not in filename:
            filename += ".xls"
        for obj_type in ("Device", "Link"):
            sheet = workbook.add_sheet(obj_type)
            for index, property in enumerate(export_properties[obj_type]):
                sheet.write(0, index, property)
                for obj_index, obj in enumerate(fetch_all(obj_type), 1):
                    sheet.write(obj_index, index, getattr(obj, property))
        workbook.save(path_app / "projects" / filename)

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
