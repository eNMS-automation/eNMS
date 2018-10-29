from flask import abort, jsonify
from flask_login import current_user, login_required
from functools import wraps
from sqlalchemy import Boolean, exc, Integer, String, Float

from eNMS import db
from eNMS.admin.models import User
from eNMS.objects.models import Link, Device, Pool
from eNMS.automation.models import Job, Service, Workflow, WorkflowEdge, service_classes
from eNMS.scheduling.models import Task

classes = {
    'Device': Device,
    'WorkflowEdge': WorkflowEdge,
    'Link': Link,
    'Pool': Pool,
    'User': User,
    'Job': Job,
    'Service': Service,
    'Workflow': Workflow,
    'Task': Task
}
