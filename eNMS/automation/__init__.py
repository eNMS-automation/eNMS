from flask import Blueprint

bp = Blueprint(
    'automation_blueprint',
    __name__,
    url_prefix='/automation',
    template_folder='templates',
    static_folder='static'
)

from eNMS.base.classes import classes
from eNMS.automation.models import Job, Service, Workflow

classes.update({'Job': Job, 'Service': Service, 'Workflow': Workflow})

import eNMS.automation.routes  # noqa: F401
