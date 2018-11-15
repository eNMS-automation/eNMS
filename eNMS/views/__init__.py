from flask import Blueprint
from pathlib import Path
from simplekml import Color, Style

from eNMS.base.properties import (
    device_subtypes,
    link_subtypes,
    link_subtype_to_color
)


bp = Blueprint(
    'views_blueprint',
    __name__,
    url_prefix='/views',
    template_folder='templates',
    static_folder='static'
)


styles, path_bp = {}, Path(bp.root_path)

for subtype in device_subtypes:
    point_style = Style()
    point_style.labelstyle.color = Color.blue
    icon = path_bp / 'static' / 'images' / 'default' / f'{subtype}.gif'
    point_style.iconstyle.icon.href = icon
    styles[subtype] = point_style

for subtype in link_subtypes:
    line_style = Style()
    # we convert the RGB color to a KML color,
    # i.e #RRGGBB to #AABBGGRR
    color = link_subtype_to_color[subtype]
    kml_color = "#ff" + color[-2:] + color[3:5] + color[1:3]
    line_style.linestyle.color = kml_color
    styles[subtype] = line_style

import eNMS.views.routes  # noqa: F401
