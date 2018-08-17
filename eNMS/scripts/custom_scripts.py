from nornir.core import Nornir
from nornir.core.inventory import Inventory
from nornir.plugins.tasks import networking
from sqlalchemy import Boolean, Column, exc, ForeignKey, Integer, String

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

## Script that does nothing


def job_example(args):
    task, node, results = args
    # add your own logic here
    # results is a dictionnary that contains the logs of the script
    results[node.name] = {
        'success': True,
        'logs': 'what will be displayed in the logs'
    }


example_parameters = {
    'name': 'script that does nothing',
    'node_multiprocessing': True,
    'description': 'does nothing',
    'vendor': 'none',
    'operating_system': 'all',
    'job_name': 'job_example'
}

## Script that uses Nornir to ping a device


def nornir_ping_job(args):
    task, node, results = args
    nornir_inventory = {node.name: {'nornir_ip': node.ip_address}}
    external = Nornir(inventory=Inventory(nornir_inventory), dry_run=True)
    ping_result = external.run(networking.tcp_ping, ports=[23, 443])
    return {
        'success': all(res for res in ping_result[node.name].result.keys()),
        'logs': str(ping_result[node.name].result)
    }


nornir_ping_parameters = {
    'name': 'nornir ping 23 443',
    'node_multiprocessing': True,
    'description': 'Uses Nornir to ping',
    'vendor': 'none',
    'operating_system': 'all',
    'job_name': 'nornir_ping_job'
}


def create_custom_scripts():
    for parameters in (
        example_parameters,
        nornir_ping_parameters
    ):
        try:
            custom_script = CustomScript(**parameters)
            db.session.add(custom_script)
            db.session.commit()
        except exc.IntegrityError:
            db.session.rollback()
