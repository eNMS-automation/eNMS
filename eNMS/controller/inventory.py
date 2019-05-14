from logging import info
from os import environ
from simplekml import Color, Style
from typing import Dict
from xlrd import open_workbook
from xlrd.biffh import XLRDError
from yaml import load, BaseLoader

from eNMS.database import Session
from eNMS.database.functions import factory, fetch_all
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
