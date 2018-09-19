from importlib.util import spec_from_file_location, module_from_spec
from json import dumps, loads
from pathlib import Path
from re import search
from requests import (
    get as rest_get,
    post as rest_post,
    put as rest_put,
    delete as rest_delete
)
from requests.auth import HTTPBasicAuth
from sqlalchemy import (
    Boolean,
    Column,
    Float,
    ForeignKey,
    Integer,
    PickleType,
    String
)
from sqlalchemy.ext.mutable import MutableDict, MutableList
from sqlalchemy.orm import relationship
from subprocess import check_output

from eNMS import db
from eNMS.base.custom_base import CustomBase
from eNMS.base.helpers import integrity_rollback
from eNMS.base.properties import property_types


def multiprocessing(function):
    def wrapper(self, args):
        task, device, results, incoming_payload = args
        success, result, payload = function(self, *args)
        if 'logs' in results:
            results['logs'][device.name] = result
            results['payload']['outgoing_payload'][device.name] = payload
        else:
            results['logs'] = {device.name: result}
            results['payload'] = {
                'incoming_payload': incoming_payload,
                'outgoing_payload': {device.name: payload}
            }
        if 'success' not in results or results['success']:
            results['success'] = success
    return wrapper


def load_module(file_location):
    spec = spec_from_file_location(file_location, file_location)
    service_module = module_from_spec(spec)
    spec.loader.exec_module(service_module)
    return service_module


class Job(CustomBase):

    __tablename__ = 'Job'

    id = Column(Integer, primary_key=True)
    name = Column(String(120), unique=True)
    description = Column(String)
    type = Column(String)

    __mapper_args__ = {
        'polymorphic_identity': 'Job',
        'polymorphic_on': type
    }


class Service(Job):

    __tablename__ = 'Service'

    id = Column(Integer, ForeignKey('Job.id'), primary_key=True)
    tasks = relationship('ServiceTask', back_populates='service')
    device_multiprocessing = False
    private = {'id'}

    __mapper_args__ = {
        'polymorphic_identity': 'service',
    }

    @property
    def properties(self):
        return {p: getattr(self, p) for p in ('name', 'description', 'type')}

    @property
    def column_values(self):
        serialized_object = self.properties
        for col in self.__table__.columns:
            value = getattr(self, col.key)
            serialized_object[col.key] = value
        return serialized_object

    @property
    def serialized(self):
        properties = self.properties
        properties['tasks'] = [
            obj.properties for obj in getattr(self, 'tasks')
        ]
        return properties





service_classes = {}


def create_custom_services():
    path_services = Path.cwd() / 'eNMS' / 'services' / 'services'
    for file in path_services.glob('**/*.py'):
        if 'init' not in str(file):
            mod = load_module(str(file))
    for cls_name, cls in service_classes.items():
        for col in cls.__table__.columns:
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
