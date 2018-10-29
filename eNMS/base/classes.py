from flask import abort, jsonify
from flask_login import current_user, login_required
from functools import wraps
from sqlalchemy import Boolean, exc, Integer, String, Float

from eNMS import db
from eNMS.admin.models import User
from eNMS.objects.models import Link, Device, Pool
from eNMS.automation.models import Job, Service, Workflow, WorkflowEdge
from eNMS.scheduling.models import Task

classes = {
    'device': Device,
    'edge': WorkflowEdge,
    'link': Link,
    'pool': Pool,
    'user': User,
    'job': Job,
    'service': Service,
    'workflow': Workflow,
    'task': Task
}
