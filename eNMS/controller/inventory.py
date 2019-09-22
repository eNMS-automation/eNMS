from collections import Counter
from difflib import SequenceMatcher
from logging import info
from pynetbox import api as netbox_api
from requests import get as http_get
from sqlalchemy import and_
from subprocess import Popen
from simplekml import Kml, Style
from typing import Any, BinaryIO, List, Union
from werkzeug.utils import secure_filename
from xlrd import open_workbook
from xlrd.biffh import XLRDError
from xlwt import Workbook

from eNMS.controller.base import BaseController
from eNMS.database import DIALECT, Session
from eNMS.database.functions import delete_all, factory, fetch, fetch_all, objectify
from eNMS.models import models, property_types
from eNMS.properties import field_conversion
from eNMS.properties.table import filtering_properties, table_properties


class InventoryController(BaseController):
    def get_gotty_port(self) -> int:
        self.gotty_port += 1
        range = self.gotty_end_port - self.gotty_start_port
        return self.gotty_start_port + self.gotty_port % range

    def connection(self, device_id: int, **kwargs: Any) -> dict:
        device = fetch("device", id=device_id)
        cmd = [str(self.path / "applications" / "gotty"), "-w"]
        port, protocol = self.get_gotty_port(), kwargs["protocol"]
        address = getattr(device, kwargs["address"])
        cmd.extend(["-p", str(port)])
        if "accept-once" in kwargs:
            cmd.append("--once")
        if "multiplexing" in kwargs:
            cmd.extend(f"tmux new -A -s gotty{port}".split())
        if self.gotty_bypass_key_prompt:
            options = "-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"
        else:
            options = ""
        if protocol == "telnet":
            cmd.extend(f"telnet {address}".split())
        elif "authentication" in kwargs:
            if kwargs["credentials"] == "device":
                login, pwd = device.username, device.password
            else:
                login, pwd = kwargs["user"].name, kwargs["user"].password
            cmd.extend(f"sshpass -p {pwd} ssh {options} {login}@{address}".split())
        else:
            cmd.extend(f"ssh {options} {address}".split())
        if protocol != "telnet":
            cmd.extend(f"-p {device.port}".split())
        Popen(cmd)
        return {
            "device": device.name,
            "port": port,
            "redirection": self.gotty_port_redirection,
            "server_addr": self.server_addr,
        }

    def get_device_logs(self, device_id: int) -> Union[str, bool]:
        device_logs = [
            log.name
            for log in fetch_all("log")
            if log.source == fetch("device", id=device_id).ip_address
        ]
        return "\n".join(device_logs)

    def clear_configurations(self, device_id: int) -> None:
        fetch("device", id=device_id).configurations = {}

    def counters(self, property: str, type: str) -> Counter:
        return Counter(str(getattr(instance, property)) for instance in fetch_all(type))

    def export_to_google_earth(self, **kwargs: Any) -> None:
        kml_file = Kml()
        for device in fetch_all("device"):
            point = kml_file.newpoint(name=device.name)
            point.coords = [(device.longitude, device.latitude)]
            point.style = self.google_earth_styles[device.icon]
            point.style.labelstyle.scale = kwargs["label_size"]
        for link in fetch_all("link"):
            line = kml_file.newlinestring(name=link.name)
            line.coords = [
                (link.source.longitude, link.source.latitude),
                (link.destination.longitude, link.destination.latitude),
            ]
            line.style = Style()
            kml_color = f"ff{link.color[5:]}{link.color[3:5]}{link.color[1:3]}"
            line.style.linestyle.color = kml_color
            line.style.linestyle.width = kwargs["line_width"]
        filepath = self.path / "projects" / "google_earth" / f'{kwargs["name"]}.kmz'
        kml_file.save(filepath)

    def export_topology(self, **kwargs: str) -> None:
        workbook = Workbook()
        filename = kwargs["export_filename"]
        if "." not in filename:
            filename += ".xls"
        for obj_type in ("device", "link"):
            sheet = workbook.add_sheet(obj_type)
            for index, property in enumerate(table_properties[obj_type]):
                sheet.write(0, index, property)
                for obj_index, obj in enumerate(fetch_all(obj_type), 1):
                    sheet.write(obj_index, index, getattr(obj, property))
        workbook.save(self.path / "projects" / "spreadsheets" / filename)

    def get_configurations(self, device_id: int) -> dict:
        return fetch("device", id=device_id).get_configurations()

    def query_netbox(self, **kwargs: str) -> None:
        nb = netbox_api(kwargs["netbox_address"], token=kwargs["netbox_token"])
        for device in nb.dcim.devices.all():
            device_ip = device.primary_ip4 or device.primary_ip6
            factory(
                "device",
                **{
                    "name": device.name,
                    "ip_address": str(device_ip).split("/")[0],
                    "subtype": str(device.device_role),
                    "model": str(device.device_type),
                    "location": str(device.site),
                    "vendor": str(device.device_type.manufacturer),
                    "operating_system": str(device.platform),
                    "longitude": str(nb.dcim.sites.get(name=device.site).longitude),
                    "latitude": str(nb.dcim.sites.get(name=device.site).latitude),
                },
            )

    def query_librenms(self, **kwargs: str) -> None:
        devices = http_get(
            f'{kwargs["librenms_address"]}/api/v0/devices',
            headers={"X-Auth-Token": kwargs["librenms_token"]},
        ).json()["devices"]
        for device in devices:
            factory(
                "device",
                **{
                    "name": device["hostname"],
                    "ip_address": device["ip"] or device["hostname"],
                    "model": device["hardware"],
                    "operating_system": device["os"],
                    "os_version": device["version"],
                    "location": device["location"],
                    "longitude": device["lng"],
                    "latitude": device["lat"],
                },
            )

    def query_opennms(self, **kwargs: str) -> None:
        login, password = self.opennms_login, kwargs["password"]
        Session.commit()
        json_devices = http_get(
            self.opennms_devices,
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
            }
            for device in json_devices
        }
        for device in list(devices):
            link = http_get(
                f"{self.opennms_rest_api}/nodes/{device}/ipinterfaces",
                headers={"Accept": "application/json"},
                auth=(login, password),
            ).json()
            for interface in link["ipInterface"]:
                if interface["snmpPrimary"] == "P":
                    devices[device]["ip_address"] = interface["ipAddress"]
                    factory("device", **devices[device])

    def topology_import(self, file: BinaryIO) -> str:
        book = open_workbook(file_contents=file.read())
        result = "Topology successfully imported."
        for obj_type in ("Device", "Link"):
            try:
                sheet = book.sheet_by_name(obj_type)
            except XLRDError:
                continue
            properties = sheet.row_values(0)
            for row_index in range(1, sheet.nrows):
                values = {"dont_update_pools": True}
                for index, property in enumerate(properties):
                    func = field_conversion[property_types[property]]
                    values[property] = func(sheet.row_values(row_index)[index])
                try:
                    factory(obj_type.lower(), **values).serialized
                except Exception as e:
                    info(f"{str(values)} could not be imported ({str(e)})")
                    result = "Partial import (see logs)."
            Session.commit()
        for pool in fetch_all("pool"):
            pool.compute_pool()
        return result

    def import_topology(self, **kwargs: Any) -> str:
        file = kwargs["file"]
        if kwargs["replace"]:
            delete_all("device")
            Session.commit()
        if self.allowed_file(secure_filename(file.filename), {"xls", "xlsx"}):
            result = self.topology_import(file)
        info("Inventory import: Done.")
        return result

    def save_pool_objects(self, pool_id: int, **kwargs: Any) -> dict:
        pool = fetch("pool", id=pool_id)
        for obj_type in ("device", "link"):
            string_value = kwargs[f"string_{obj_type}s"]
            setattr(
                pool,
                f"{obj_type}s",
                (
                    [
                        fetch(obj_type, name=name)
                        for name in string_value.strip().split(",")
                    ]
                    if string_value
                    else objectify(obj_type, kwargs[f"{obj_type}s"])
                ),
            )
        return pool.serialized

    def update_pool(self, pool_id: str) -> None:
        fetch("pool", id=int(pool_id)).compute_pool()

    def update_all_pools(self) -> None:
        for pool in fetch_all("pool"):
            pool.compute_pool()

    def get_view_topology(self) -> dict:
        return {
            "devices": [d.view_properties for d in fetch_all("device")],
            "links": [d.view_properties for d in fetch_all("link")],
        }

    def view_filtering(self, obj_type: str, kwargs: Any) -> List[dict]:
        constraints = self.build_filtering_constraints(obj_type, kwargs)
        result = Session.query(models[obj_type]).filter(and_(*constraints))
        return [d.view_properties for d in result.all()]
