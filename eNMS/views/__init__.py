from flask import Blueprint
from os.path import join
from simplekml import Color, Style


from eNMS.objects.models import node_subtypes, link_class


blueprint = Blueprint(
    'views_blueprint',
    __name__,
    url_prefix='/views',
    template_folder='templates',
    static_folder='static'
)


styles = {}

for subtype in node_subtypes:
    point_style = Style()
    point_style.labelstyle.color = Color.blue
    path_icon = join(blueprint.root_path, 'static', 'images', 'default', subtype + '.gif')
    point_style.iconstyle.icon.href = path_icon
    styles[subtype] = point_style

for subtype, cls in link_class.items():
    line_style = Style()
    # we convert the RGB color to a KML color,
    # i.e #RRGGBB to #AABBGGRR
    kml_color = "#ff" + cls.color[-2:] + cls.color[3:5] + cls.color[1:3]
    line_style.linestyle.color = kml_color
    styles[subtype] = line_style

from . import routes
