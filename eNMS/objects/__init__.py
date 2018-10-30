from flask import Blueprint

bp = Blueprint(
    'objects_blueprint',
    __name__,
    url_prefix='/objects',
    template_folder='templates',
    static_folder='static'
)

from eNMS.base.helpers import add_classes
from eNMS.objects.models import Device, Link, Pool

add_classes(Device, Link, Pool)

import eNMS.objects.routes  # noqa: F401
