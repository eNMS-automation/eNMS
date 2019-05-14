from collections import Counter
from datetime import datetime
from difflib import SequenceMatcher
from logging import info
from os import environ
from simplekml import Color, Kml, Style
from typing import Dict, Union
from xlrd import open_workbook
from xlrd.biffh import XLRDError
from yaml import load, BaseLoader

from eNMS.database import Session
from eNMS.database.functions import factory, fetch, fetch_all
from eNMS.models import property_types
from eNMS.properties import field_conversion, property_names
from eNMS.properties.objects import (
    device_properties,
    device_subtypes,
    link_colors,
    link_subtypes,
    pool_device_properties,
)


class InventoryController:
    def get_configuration_diff(self, device_id: int, v1: str, v2: str) -> dict:
        device = fetch("Device", id=device_id)
        d1, d2 = [datetime.strptime(d, "%Y+%m+%d %H:%M:%S.%f") for d in (v1, v2)]
        first = device.configurations[d1].splitlines()
        second = device.configurations[d2].splitlines()
        opcodes = SequenceMatcher(None, first, second).get_opcodes()
        return {"first": first, "second": second, "opcodes": opcodes}

    def get_device_logs(self, device_id: int) -> Union[str, bool]:
        device_logs = [
            log.name
            for log in fetch_all("Log")
            if log.source == fetch("Device", id=device_id).ip_address
        ]
        return "\n".join(device_logs)

    def create_google_earth_styles(self) -> None:
        self.google_earth_styles: Dict[str, Style] = {}
        for subtype in device_subtypes:
            point_style = Style()
            point_style.labelstyle.color = Color.blue
            path_icon = f"{self.app.path}/eNMS/views/static/images/2D/{subtype}.gif"
            point_style.iconstyle.icon.href = path_icon
            self.google_earth_styles[subtype] = point_style
        for subtype in link_subtypes:
            line_style = Style()
            color = link_colors[subtype]
            kml_color = "#ff" + color[-2:] + color[3:5] + color[1:3]
            line_style.linestyle.color = kml_color
            self.google_earth_styles[subtype] = line_style

    def export_to_google_earth(self, parameters) -> None:
        kml_file = Kml()
        for device in fetch_all("Device"):
            point = kml_file.newpoint(name=device.name)
            point.coords = [(device.longitude, device.latitude)]
            point.style = self.google_earth_styles[device.subtype]
            point.style.labelstyle.scale = parameters["label_size"]
        for link in fetch_all("Link"):
            line = kml_file.newlinestring(name=link.name)
            line.coords = [
                (link.source.longitude, link.source.latitude),
                (link.destination.longitude, link.destination.latitude),
            ]
            line.style = self.google_earth_styles[link.subtype]
            line.style.linestyle.width = parameters["line_width"]
        filepath = self.app.path / "google_earth" / f'{parameters["name"]}.kmz'
        kml_file.save(filepath)

    def load_custom_properties(self) -> dict:
        filepath = environ.get("PATH_CUSTOM_PROPERTIES")
        if not filepath:
            custom_properties = {}
        else:
            with open(filepath, "r") as properties:
                custom_properties = load(properties, Loader=BaseLoader)
        property_names.update(
            {k: v["property_name"] for k, v in custom_properties.items()}
        )
        for object_properties in (device_properties, pool_device_properties):
            object_properties.extend(list(custom_properties))
        return custom_properties

    def topology_import(self, file):
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
        Session.commit()
        return result
