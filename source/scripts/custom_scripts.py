from base.database import Base, db
from .models import Script, type_to_class
from nornir.core import Nornir
from nornir.core.inventory import Inventory
from nornir.plugins.tasks import networking
from sqlalchemy import Column, exc, ForeignKey, Integer, String


class JobStore(Base):

    __tablename__ = 'JobStore'

    id = Column(Integer, primary_key=True)

    def job_example(self, args):
        task, node, results = args
        # add your own logic here
        # results is a dictionnary that contains the logs of the script
        results[node.name] = 'what will be displayed in the logs'
        # a script returns a boolean value used in workflows (see the workflow section)
        return True if 'a condition for success' else False

    def nornir_ping_job(self, args):
        task, node, results = args
        nornir_inventory = {node.name: {'nornir_ip': node.ip_address}}
        external = Nornir(inventory=Inventory(nornir_inventory), dry_run=True)
        ping_result = external.run(networking.tcp_ping, ports=[23, 443])
        results[node.name] = str(ping_result[node.name].result)
        return all(res for res in ping_result[node.name].result.keys())


class CustomScript(Script):

    __tablename__ = 'CustomScript'

    id = Column(Integer, ForeignKey('Script.id'), primary_key=True)
    job_name = Column(String)
    vendor = Column(String)
    operating_system = Column(String)

    __mapper_args__ = {
        'polymorphic_identity': 'custom_script',
    }

    def __init__(self, **kwargs):
        self.__dict__.update(**kwargs)
        name = kwargs['name']
        waiting_time = kwargs['waiting_time']
        description = kwargs['description']
        super(CustomScript, self).__init__(name, waiting_time, description)

    def job(self, args):
        job_store = db.session.query(JobStore).one()
        getattr(job_store, self.job_name)(args)


type_to_class['custom_script'] = CustomScript

## Script that does nothing

example_parameters = {
    'name': 'script that does nothing',
    'waiting_time': 0,
    'description': 'does nothing',
    'vendor': 'none',
    'operating_system': 'all',
    'job_name': 'job_example'
}

## Script that uses Nornir to ping a device

nornir_ping_parameters = {
    'name': 'nornir ping 23 443',
    'waiting_time': 0,
    'description': 'Uses Nornir to ping',
    'vendor': 'none',
    'operating_system': 'all',
    'job_name': 'nornir_ping_job'
}


def create_custom_scripts():
    job_store = JobStore()
    db.session.add(job_store)
    db.session.commit()
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
