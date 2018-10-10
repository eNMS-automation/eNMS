from flask import jsonify, render_template, request
from flask_login import login_required

from eNMS import db
from eNMS.base.custom_base import factory
from eNMS.base.helpers import permission_required, retrieve
from eNMS.base.properties import pretty_names, workflow_table_properties
from eNMS.objects.models import Device, Pool
from eNMS.services.forms import CompareLogsForm
from eNMS.services.models import Job
from eNMS.tasks.models import Task
from eNMS.tasks.forms import SchedulingForm
from eNMS.workflows import blueprint
from eNMS.workflows.forms import (
    AddJobForm,
    WorkflowEditorForm,
    WorkflowCreationForm
)
from eNMS.workflows.models import WorkflowEdge, Workflow






