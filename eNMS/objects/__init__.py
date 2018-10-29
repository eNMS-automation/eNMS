from flask import Blueprint

bp = Blueprint(
    'objects_blueprint',
    __name__,
    url_prefix='/objects',
    template_folder='templates',
    static_folder='static'
)

from eNMS.base.models import classes
from eNMS.objects.models import Device, Link, Pool
classes.update({'Device': Device, 'Link': Link, 'Pool': Pool})
import eNMS.objects.routes  # noqa: F401
