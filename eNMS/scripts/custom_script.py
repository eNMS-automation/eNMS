from importlib.util import spec_from_file_location, module_from_spec
from pathlib import Path
from sqlalchemy import Boolean, Column, exc, ForeignKey, Integer, String

from eNMS import db
from eNMS.scripts.models import Script, type_to_class


def load_module(file_location):
    spec = spec_from_file_location(file_location, file_location)
    script_module = module_from_spec(spec)
    spec.loader.exec_module(script_module)
    return script_module


class CustomScript(Script):

    __tablename__ = 'CustomScript'

    id = Column(Integer, ForeignKey('Script.id'), primary_key=True)
    job_name = Column(String)
    module_location = Column(String)
    vendor = Column(String)
    operating_system = Column(String)
    device_multiprocessing = Column(Boolean, default=False)

    __mapper_args__ = {
        'polymorphic_identity': 'custom_script',
    }

    def __init__(self, **kwargs):
        self.__dict__.update(**kwargs)

    def job(self, args):
        script_module = load_module(self.module_location)
        return getattr(script_module, 'job')(self, args)


type_to_class['custom_script'] = CustomScript


def create_custom_scripts():
    path_scripts = Path.cwd() / 'eNMS' / 'scripts' / 'custom_scripts'
    for file in path_scripts.glob('**/*.py'):
        script_module = load_module(str(file))
        try:
            custom_script = CustomScript(**{
                **getattr(script_module, 'parameters'),
                'module_location': str(file)
            })
            db.session.add(custom_script)
            db.session.commit()
        except exc.IntegrityError:
            db.session.rollback()
