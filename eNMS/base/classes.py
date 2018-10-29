from flask import abort, jsonify
from flask_login import current_user, login_required
from functools import wraps
from importlib.util import spec_from_file_location, module_from_spec
from pathlib import Path
from sqlalchemy import Boolean, Float, Integer, PickleType

from eNMS import db
from eNMS.admin.models import Parameters, User
from eNMS.base.properties import (
    property_types,
    boolean_properties,
    service_import_properties,
    service_properties
)
from eNMS.objects.models import Link, Device, Pool
from eNMS.automation.models import Job, Service, Workflow, WorkflowEdge
from eNMS.scheduling.models import Task

classes = {
    'Device': Device,
    'WorkflowEdge': WorkflowEdge,
    'Link': Link,
    'Parameters': Parameters,
    'Pool': Pool,
    'User': User,
    'Job': Job,
    'Service': Service,
    'Workflow': Workflow,
    'Task': Task
}

service_classes = {}


def create_service_classes():
    path_services = Path.cwd() / 'eNMS' / 'automation' / 'services'
    for file in path_services.glob('**/*.py'):
        if 'init' not in str(file):
            spec = spec_from_file_location(str(file), str(file))
            spec.loader.exec_module(module_from_spec(spec))
    for cls_name, cls in service_classes.items():
        for col in cls.__table__.columns:
            service_properties[cls_name].append(col.key)
            service_import_properties.append(col.key)
            if type(col.type) == Boolean:
                boolean_properties.append(col.key)
            if (
                type(col.type) == PickleType
                and hasattr(cls, f'{col.key}_values')
            ):
                property_types[col.key] = list
            else:
                property_types[col.key] = {
                    Boolean: bool,
                    Integer: int,
                    Float: float,
                    PickleType: dict,
                }.get(type(col.type), str)


create_service_classes()
classes.update(service_classes)
