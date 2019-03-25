from flask import Blueprint


bp = Blueprint(
    "views_blueprint",
    __name__,
    url_prefix="/views",
    template_folder="templates",
    static_folder="static",
)

import eNMS.views.routes  # noqa: F401
