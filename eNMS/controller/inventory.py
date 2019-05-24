from collections import Counter
from difflib import SequenceMatcher
from logging import info
from pynetbox import api as netbox_api
from requests import get as http_get
from sqlalchemy import and_
from subprocess import Popen
from simplekml import Kml
from typing import Any, BinaryIO, List, Union
from werkzeug.utils import secure_filename
from xlrd import open_workbook
from xlrd.biffh import XLRDError
from xlwt import Workbook

from eNMS.controller.base import BaseController
from eNMS.database import Session
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
        device = fetch("Device", id=device_id)
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
            "server_addr": self.enms_server_addr,
        }

    def get_configuration_diff(self, device_id: int, v1: str, v2: str) -> dict:
        device = fetch("Device", id=device_id)
        first = device.configurations[v1].splitlines()
        second = device.configurations[v2].splitlines()
        opcodes = SequenceMatcher(None, first, second).get_opcodes()
        return {"first": first, "second": second, "opcodes": opcodes}

    def get_device_logs(self, device_id: int) -> Union[str, bool]:
        device_logs = [
            log.name
            for log in fetch_all("Log")
            if log.source == fetch("Device", id=device_id).ip_address
        ]
        return "\n".join(device_logs)

    def clear_configurations(self, device_id: int) -> None:
        fetch("Device", id=device_id).configurations = {}

    def counters(self, property: str, type: str) -> Counter:
        return Counter(str(getattr(instance, property)) for instance in fetch_all(type))

    def export_to_google_earth(self, **kwargs: Any) -> None:
        kml_file = Kml()
        for device in fetch_all("Device"):
            point = kml_file.newpoint(name=device.name)
            point.coords = [(device.longitude, device.latitude)]
            point.style = self.google_earth_styles[device.subtype]
            point.style.labelstyle.scale = kwargs["label_size"]
        for link in fetch_all("Link"):
            line = kml_file.newlinestring(name=link.name)
            line.coords = [
                (link.source.longitude, link.source.latitude),
                (link.destination.longitude, link.destination.latitude),
            ]
            line.style = self.google_earth_styles[link.subtype]
            line.style.linestyle.width = kwargs["line_width"]
        filepath = self.path / "projects" / "google_earth" / f'{kwargs["name"]}.kmz'
        kml_file.save(filepath)

    def export_topology(self, **kwargs: str) -> None:
        workbook = Workbook()
        filename = kwargs["export_filename"]
        if "." not in filename:
            filename += ".xls"
        for obj_type in ("device", "link"):
            sheet = workbook.add_sheet(obj_type.capitalize())
            for index, property in enumerate(table_properties[obj_type]):
                sheet.write(0, index, property)
                for obj_index, obj in enumerate(fetch_all(obj_type), 1):
                    sheet.write(obj_index, index, getattr(obj, property))
        workbook.save(self.path / "projects" / "spreadsheets" / filename)

    def get_configurations(self, device_id: int) -> dict:
        return fetch("Device", id=device_id).get_configurations()

    def query_netbox(self, **kwargs: str) -> None:
        nb = netbox_api(kwargs["netbox_address"], token=kwargs["netbox_token"])
        for device in nb.dcim.devices.all():
            device_ip = device.primary_ip4 or device.primary_ip6
            factory(
                "Device",
                **{
                    "name": device.name,
                    "ip_address": str(device_ip).split("/")[0],
                    "subtype": kwargs["netbox_type"],
                    "longitude": 0.0,
                    "latitude": 0.0,
                },
            )

    def query_librenms(self, **kwargs: str) -> None:
        devices = http_get(
            f'{kwargs["librenms_address"]}/api/v0/devices',
            headers={"X-Auth-Token": kwargs["librenms_token"]},
        ).json()["devices"]
        for device in devices:
            factory(
                "Device",
                **{
                    "name": device["hostname"],
                    "ip_address": device["ip"] or device["hostname"],
                    "subtype": kwargs["librenms_type"],
                    "longitude": 0.0,
                    "latitude": 0.0,
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
                "subtype": kwargs["subtype"],
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
                    factory("Device", **devices[device])

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
                    factory(obj_type, **values).serialized
                except Exception as e:
                    info(f"{str(values)} could not be imported ({str(e)})")
                    result = "Partial import (see logs)."
            Session.commit()
        for pool in fetch_all("Pool"):
            pool.compute_pool()
        return result

    def import_topology(self, **kwargs: Any) -> str:
        file = kwargs["file"]
        if kwargs["replace"]:
            delete_all("Device")
            Session.commit()
        if self.allowed_file(secure_filename(file.filename), {"xls", "xlsx"}):
            result = self.topology_import(file)
        info("Inventory import: Done.")
        return result

    def save_pool_objects(self, pool_id: int, kwargs: Any) -> dict:
        pool = fetch("Pool", id=pool_id)
        pool.devices = objectify("Device", kwargs["devices"])
        pool.links = objectify("Link", kwargs["links"])
        return pool.serialized

    def update_pools(self, pool_id: str) -> None:
        if pool_id == "all":
            for pool in fetch_all("Pool"):
                pool.compute_pool()
        else:
            fetch("Pool", id=int(pool_id)).compute_pool()

    def get_view_topology(self) -> dict:
        return {
            "devices": [d.view_properties for d in fetch_all("Device")],
            "links": [d.view_properties for d in fetch_all("Link")],
        }

    def view_filtering(self, filter_type: str, **kwargs: Any) -> List[dict]:
        obj_type = filter_type.split("_")[0]
        model = models[obj_type]
        constraints = []
        for property in filtering_properties[obj_type]:
            value = kwargs[property]
            if value:
                constraints.append(getattr(model, property).contains(value))
        result = Session.query(model).filter(and_(*constraints))
        pools = [int(id) for id in kwargs["pools"]]
        if pools:
            result = result.filter(model.pools.any(models["pool"].id.in_(pools)))
        return [d.view_properties for d in result.all()]
