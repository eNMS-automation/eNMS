from base.database import db
from base.helpers import integrity_rollback
from .models import Script, type_to_class
from nornir.core import Nornir
from nornir.core.inventory import Inventory
from nornir.plugins.tasks import networking
from sqlalchemy import Column, ForeignKey, Integer, String


class CustomScript(Script):

    __tablename__ = 'CustomScript'

    id = Column(Integer, ForeignKey('Script.id'), primary_key=True)
    vendor = Column(String)
    operating_system = Column(String)

    __mapper_args__ = {
        'polymorphic_identity': 'custom_script',
    }


type_to_class['custom_script'] = CustomScript


class CustomScriptExample(CustomScript):

    __tablename__ = 'CustomScriptExample'

    id = Column(Integer, ForeignKey('CustomScript.id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': 'custom_script_example',
    }

    def __init__(self):
        name = 'custom_script_example'
        waiting_time = 0
        description = 'script_description'
        self.vendor = 'a vendor'
        self.operating_system = 'an operating system'
        super(CustomScriptExample, self).__init__(name, waiting_time, description)

    def job(self, args):
        task, node, results = args
        # add your own logic here
        # results is a dictionnary that contains the logs of the script
        results[node.name] = 'what will be displayed in the logs'
        # a script returns a boolean value used in workflows (see the workflow section)
        return True if 'a condition for success' else False


class NornirPingScript(CustomScript):

    __tablename__ = 'NornirPingScript'

    id = Column(Integer, ForeignKey('CustomScript.id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': 'nornir_ping_config',
    }

    def __init__(self):
        name = 'nornir_ping_script'
        waiting_time = 0
        description = 'script_description'
        self.vendor = 'a vendor'
        self.operating_system = 'an operating system'
        super(NornirPingScript, self).__init__(name, waiting_time, description)

    def job(self, args):
        task, node, results = args
        nornir_inventory = {node.name: {'nornir_ip': node.ip_address}}
        external = Nornir(inventory=Inventory(nornir_inventory), dry_run=True)
        ping_result = external.run(networking.tcp_ping, ports=[23, 443])
        results[node.name] = str(ping_result[node.name].result)
        return all(res for res in ping_result[node.name].result.keys())


@integrity_rollback
def create_custom_scripts():
    for custom_script in (
        CustomScriptExample,
        NornirPingScript
    ):
        db.session.add(custom_script())
        db.session.commit()
