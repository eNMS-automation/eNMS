from flask import Blueprint

bp = Blueprint(
    'logs_blueprint',
    __name__,
    url_prefix='/logs',
    template_folder='templates',
    static_folder='static'
)

from eNMS.base.helpers import add_classes
from eNMS.logs.models import Log, LogRule, SyslogServer

add_classes(Log, LogRule, SyslogServer)

import eNMS.logs.routes  # noqa: F401
