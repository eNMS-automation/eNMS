from flask import Blueprint

bp = Blueprint(
    'scheduling_blueprint',
    __name__,
    url_prefix='/scheduling',
    template_folder='templates',
    static_folder='static'
)

from eNMS.base.helpers import add_classes
from eNMS.scheduling.models import Task

add_classes(Task)

import eNMS.scheduling.routes  # noqa: F401
