from flask import Blueprint

bp = Blueprint(
    'inventory_blueprint',
    __name__,
    url_prefix='/inventory',
    template_folder='templates',
    static_folder='static'
)

from eNMS.base.helpers import add_classes
from eNMS.inventory.models import Device, Link, Object, Pool

add_classes(Device, Link, Object, Pool)

import eNMS.inventory.routes  # noqa: F401
