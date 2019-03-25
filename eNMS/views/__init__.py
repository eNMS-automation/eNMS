from flask import Blueprint

from eNMS.base.properties import device_subtypes, link_subtypes, link_subtype_to_color


bp = Blueprint(
    "views_blueprint",
    __name__,
    url_prefix="/views",
    template_folder="templates",
    static_folder="static",
)

import eNMS.views.routes  # noqa: F401
