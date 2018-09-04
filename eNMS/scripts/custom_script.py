from pathlib import Path
from sqlalchemy import Boolean, Column, exc, ForeignKey, Integer, String

from nornir.core import Nornir
from nornir.core.inventory import Inventory
from nornir.plugins.tasks import networking


from eNMS import db
from eNMS.scripts.models import Script, type_to_class


class CustomScript(Script):

    __tablename__ = 'CustomScript'

    id = Column(Integer, ForeignKey('Script.id'), primary_key=True)
    job_name = Column(String)
    vendor = Column(String)
    operating_system = Column(String)
    node_multiprocessing = Column(Boolean, default=False)

    __mapper_args__ = {
        'polymorphic_identity': 'custom_script',
    }

    def __init__(self, **kwargs):
        self.__dict__.update(**kwargs)

    def job(self, args):
        globals()[self.job_name](args)


type_to_class['custom_script'] = CustomScript


# 
# 
# def nornir_ping_job(args):
#     # Script that uses Nornir to ping a device
#     task, node, results = args
#     nornir_inventory = {node.name: {'nornir_ip': node.ip_address}}
#     external = Nornir(inventory=Inventory(nornir_inventory), dry_run=True)
#     ping_result = external.run(networking.tcp_ping, ports=[23, 443])
#     return {
#         'success': all(res for res in ping_result[node.name].result.keys()),
#         'logs': str(ping_result[node.name].result)
#     }
# 
# 
# nornir_ping_parameters = {
#     'name': 'nornir ping 23 443',
#     'node_multiprocessing': True,
#     'description': 'Uses Nornir to ping',
#     'vendor': 'none',
#     'operating_system': 'all',
#     'job_name': 'nornir_ping_job'
# }

import importlib
import importlib.util
from inspect import getmembers
def create_custom_scripts():
    path_scripts = Path.cwd() / 'eNMS' / 'scripts' / 'custom_scripts'
    for file in path_scripts.glob('**/*.py'):
        if file == '__init__.py':
            print('pass')
            pass
        spec = importlib.util.spec_from_file_location(str(file), file)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        try:
            custom_script = CustomScript(**getattr(mod, 'parameters'))
            db.session.add(custom_script)
            db.session.commit()
        except exc.IntegrityError:
            db.session.rollback()
