from flask import Blueprint

bp = Blueprint(
    'scheduling_blueprint',
    __name__,
    url_prefix='/scheduling',
    template_folder='templates',
    static_folder='static'
)

from eNMS.base.classes import classes
from eNMS.scheduling.models import Task

classes['Task'] = Task
import eNMS.scheduling.routes  # noqa: F401
