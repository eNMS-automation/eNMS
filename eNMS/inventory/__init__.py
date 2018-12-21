from flask import Blueprint

bp = Blueprint(
    'objects_blueprint',
    __name__,
    url_prefix='/objects',
    template_folder='templates',
    static_folder='static'
)

from eNMS.base.helpers import add_classes
from eNMS.inventory.models import Device, Link, Object, Pool

add_classes(Device, Link, Object, Pool)

import eNMS.inventory.routes  # noqa: F401
