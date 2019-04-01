from flask import Blueprint

bp = Blueprint(
    "automation_blueprint",
    __name__,
    url_prefix="/automation",
    template_folder="templates",
    static_folder="static",
)

from eNMS.automation.models import Job, Service, Workflow, WorkflowEdge
from eNMS.functions import add_classes

add_classes(Job, Service, Workflow, WorkflowEdge)

import eNMS.automation.routes  # noqa: F401
