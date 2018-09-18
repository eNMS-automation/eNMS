from importlib.util import spec_from_file_location, module_from_spec
from pathlib import Path
from sqlalchemy import Boolean, Column, exc, ForeignKey, Integer, String

from eNMS import db
from eNMS.base.helpers import integrity_rollback
from eNMS.services.models import Service, type_to_class


def load_module(file_location):
    spec = spec_from_file_location(file_location, file_location)
    service_module = module_from_spec(spec)
    spec.loader.exec_module(service_module)
    return service_module


class CustomService(Service):

    __tablename__ = 'CustomService'

    id = Column(Integer, ForeignKey('Service.id'), primary_key=True)
    vendor = Column(String)
    operating_system = Column(String)
    device_multiprocessing = Column(Boolean, default=False)

    __mapper_args__ = {
        'polymorphic_identity': 'custom_service',
    }

    def __init__(self, **kwargs):
        self.__dict__.update(**kwargs)


type_to_class['custom_service'] = CustomService
service_classes = {}


def create_custom_services():
    path_services = Path.cwd() / 'eNMS' / 'services' / 'custom_services'
    for file in path_services.glob('**/*.py'):
        if 'init' not in str(file):
            mod = load_module(str(file))


@integrity_rollback
def create_custom_service_instances():
    for i in range(3):
        for cls_name, cls in service_classes.items():
            s = cls(**{'name': cls_name + 'oook' + str(i)})
            db.session.add(s)
            db.session.commit()
