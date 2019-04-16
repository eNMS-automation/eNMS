from flask import Blueprint

bp = Blueprint(
    "home_blueprint",
    __name__,
    url_prefix="/home",
    template_folder="templates",
    static_folder="static",
)

from eNMS.functions import add_classes
from eNMS.home.models import Log, SyslogServer

add_classes(Log, SyslogServer)

import eNMS.home.routes  # noqa: F401
