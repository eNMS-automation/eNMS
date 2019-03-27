from flask import Blueprint
from importlib import reload
from importlib.abc import Loader
from importlib.util import spec_from_file_location, module_from_spec
from os import environ
from pathlib import Path
from sqlalchemy import Boolean, Float, Integer, PickleType

bp = Blueprint(
    "automation_blueprint",
    __name__,
    url_prefix="/automation",
    template_folder="templates",
    static_folder="static",
)

from eNMS.automation.models import Job, Service, Workflow, WorkflowEdge
from eNMS.base.functions import add_classes

add_classes(Job, Service, Workflow, WorkflowEdge)

import eNMS.automation.routes  # noqa: F401
