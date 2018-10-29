from flask import Blueprint

bp = Blueprint(
    'objects_blueprint',
    __name__,
    url_prefix='/objects',
    template_folder='templates',
    static_folder='static'
)

from eNMS.base.classes import classes
from eNMS.objects.models import Device
import eNMS.objects.routes  # noqa: F401
