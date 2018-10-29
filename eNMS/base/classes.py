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


def factory(cls, **kwargs):
    if 'id' in kwargs:
        instance = fetch(cls, id=kwargs['id'])
    else:
        instance = fetch(cls, name=kwargs['name'])
    if instance:
        instance.update(**kwargs)
    else:
        instance = cls(**kwargs)
        db.session.add(instance)
    db.session.commit()
    return instance


def fetch(model, **kwargs):
    return db.session.query(model).filter_by(**kwargs).first()


def objectify(model, object_list):
    return [fetch(model, id=object_id) for object_id in object_list]
