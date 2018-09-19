from importlib.util import spec_from_file_location, module_from_spec
from pathlib import Path
from sqlalchemy import (
    Boolean,
    Column,
    Float,
    ForeignKey,
    Integer,
    PickleType,
    String
)

from eNMS import db
from eNMS.base.helpers import integrity_rollback
from eNMS.base.properties import property_types
from eNMS.services.models import Service, type_to_class


def load_module(file_location):
    spec = spec_from_file_location(file_location, file_location)
    service_module = module_from_spec(spec)
    spec.loader.exec_module(service_module)
    return service_module


class CustomService(Service):

    __tablename__ = 'CustomService'

    id = Column(Integer, ForeignKey('Service.id'), primary_key=True)
    device_multiprocessing = False
    private = {'id'}

    __mapper_args__ = {
        'polymorphic_identity': 'custom_service',
    }

    @property
    def serialized(self):
        serialized_object = {'name': self.name}
        for col in self.__table__.columns:
            value = getattr(self, col.key)
            serialized_object[col.key] = value
        return serialized_object


type_to_class['custom_service'] = CustomService
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
