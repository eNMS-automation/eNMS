try:
    from ansible.parsing.dataloader import DataLoader
    from ansible.vars.manager import VariableManager
    from ansible.inventory.manager import InventoryManager
    from ansible.executor.playbook_executor import PlaybookExecutor
except Exception:
    import warnings
    warnings.warn('ansible import failed: ansible feature deactivated')
from base.database import db, get_obj
from base.helpers import str_dict
from base.models import script_workflow_table, task_script_table, CustomBase
from collections import namedtuple
from .forms import ansible_options
from napalm import get_network_driver
from netmiko import ConnectHandler
from passlib.hash import cisco_type7
from sqlalchemy import Column, Float, ForeignKey, Integer, PickleType, String
from sqlalchemy.ext.mutable import MutableDict, MutableList
from sqlalchemy.orm import relationship
from tempfile import NamedTemporaryFile


class Script(CustomBase):

    __tablename__ = 'Script'

    id = Column(Integer, primary_key=True)
    name = Column(String(120), unique=True)
    type = Column(String)
    vendor = Column(String)
    operating_system = Column(String)
    tasks = relationship(
        "Task",
        secondary=task_script_table,
        back_populates="scripts"
    )
    workflows = relationship(
        "Workflow",
        secondary=script_workflow_table,
        back_populates="scripts"
    )

    __mapper_args__ = {
        'polymorphic_identity': 'Script',
        'polymorphic_on': type
    }

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return str(self.name)

    def script_neighbors(self, workflow, type):
        return [
            x.destination for x in self.destinations
            if x.workflow == workflow and x.type == type
        ]


class NetmikoConfigScript(Script):

    __tablename__ = 'NetmikoConfigScript'

    id = Column(Integer, ForeignKey('Script.id'), primary_key=True)
    content = Column(String)
    driver = Column(String)
    global_delay_factor = Column(Float)
    netmiko_type = Column(String)

    __mapper_args__ = {
        'polymorphic_identity': 'netmiko_config',
    }

    def __init__(self, real_content, **data):
        name = data['name'][0]
        self.driver = data['driver'][0]
        self.global_delay_factor = data['global_delay_factor'][0]
        self.netmiko_type = data['netmiko_type'][0]
        super(NetmikoConfigScript, self).__init__(name)
        self.content = ''.join(real_content)

    def job(self, args):
        task, node, results = args
        try:
            netmiko_handler = ConnectHandler(
                device_type=self.driver,
                ip=node.ip_address,
                username=task.user.name,
                password=cisco_type7.decode(task.user.password),
                secret=node.secret_password
            )
            if self.netmiko_type == 'configuration':
                netmiko_handler.send_config_set(self.content.splitlines())
                result = 'configuration OK'
            else:
                # script_type is 'show_commands':
                outputs = []
                for show_command in self.content.splitlines():
                    outputs.append(netmiko_handler.send_command(show_command))
                result = '\n\n'.join(outputs)
        except Exception as e:
            result = 'netmiko config did not work because of {}'.format(e)
        try:
            netmiko_handler.disconnect()
        except Exception:
            pass
        results[node.name] = result


class FileTransferScript(Script):

    __tablename__ = 'FileTransferScript'

    id = Column(Integer, ForeignKey('Script.id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': 'file_transfer',
    }

    def __init__(self, **data):
        name = data['name'][0]
        self.source_file = data['source_file'][0]
        self.destination_file = data['destination_file'][0]
        self.file_system = data['file_system'][0]
        self.direction = data['direction'][0]
        super(FileTransferScript, self).__init__(name)

    def job(self, args):
        task, node, results = args
        try:
            netmiko_handler = ConnectHandler(
                device_type=self.driver,
                ip=node.ip_address,
                username=task.user.name,
                password=cisco_type7.decode(task.user.password),
                secret=node.secret_password
            )
            # still in netmiko develop branch for now
            file_transfer = lambda *a, **kw: 1
            transfer_dict = file_transfer(
                netmiko_handler,
                source_file=self.source_file,
                dest_file=self.dest_file,
                file_system=self.file_system,
                direction=self.direction,
                overwrite_file=False,
                disable_md5=False,
                inline_transer=False
            )
            result = str(transfer_dict)
            netmiko_handler.disconnect()
        except Exception as e:
            result = 'netmiko config did not work because of {}'.format(e)
        results[node.name] = result


class NapalmConfigScript(Script):

    __tablename__ = 'NapalmConfigScript'

    id = Column(Integer, ForeignKey('Script.id'), primary_key=True)
    content = Column(String)

    __mapper_args__ = {
        'polymorphic_identity': 'napalm_config',
    }

    def __init__(self, real_content, **data):
        name = data['name'][0]
        super(NapalmConfigScript, self).__init__(name)
        self.content = ''.join(real_content)

    def job(self, args):
        task, node, results = args
        try:
            driver = get_network_driver(node.operating_system)
            napalm_driver = driver(
                hostname=node.ip_address,
                username=task.user.name,
                password=cisco_type7.decode(task.user.password),
                optional_args={'secret': node.secret_password}
            )
            napalm_driver.open()
            if self.action in ('load_merge_candidate', 'load_replace_candidate'):
                getattr(napalm_driver, self.action)(config=self.content)
            else:
                getattr(napalm_driver, self.action)()
            napalm_driver.close()
        except Exception as e:
            result = 'napalm config did not work because of {}'.format(e)
            success = False
        else:
            result = 'configuration OK'
            success = True
        results[node.name] = result
        return success


class NapalmActionScript(Script):

    __tablename__ = 'NapalmActionScript'

    id = Column(Integer, ForeignKey('Script.id'), primary_key=True)
    action = Column(String, unique=True)

    __mapper_args__ = {
        'polymorphic_identity': 'napalm_action',
    }

    def __init__(self, name, action):
        self.action = action
        super(NapalmActionScript, self).__init__(name)

    def job(self, args):
        task, node, results = args
        try:
            driver = get_network_driver(node.operating_system)
            napalm_driver = driver(
                hostname=node.ip_address,
                username=task.user.name,
                password=cisco_type7.decode(task.user.password),
                optional_args={'secret': node.secret_password}
            )
            napalm_driver.open()
            getattr(napalm_driver, self.action)()
            napalm_driver.close()
        except Exception as e:
            result = 'napalm {} did not work because of {}'.format(self.action, e)
            success = False
        else:
            result = self.action + ' OK'
            success = True
        results[node.name] = result
        return success


class NapalmGettersScript(Script):

    __tablename__ = 'NapalmGettersScript'

    id = Column(Integer, ForeignKey('Script.id'), primary_key=True)
    getters = Column(MutableList.as_mutable(PickleType), default=[])

    __mapper_args__ = {
        'polymorphic_identity': 'napalm_getters',
    }

    def __init__(self, **data):
        name = data['name'][0]
        self.getters = data['getters']
        super(NapalmGettersScript, self).__init__(name)

    def job(self, args):
        task, node, results = args
        try:
            driver = get_network_driver(node.operating_system)
            napalm_driver = driver(
                hostname=node.ip_address,
                username=task.user.name,
                password=cisco_type7.decode(task.user.password),
                optional_args={'secret': node.secret_password}
            )
            napalm_driver.open()
            for getter in self.getters:
                try:
                    result = str_dict(getattr(napalm_driver, getter)())
                except Exception as e:
                    result = '{} could not be retrieve because of {}'.format(getter, e)
            napalm_driver.close()
        except Exception as e:
            result = 'getters process did not work because of {}'.format(e)
            success = False
        else:
            success = True
            results[node.name] = result
        return success


class AnsibleScript(Script):

    __tablename__ = 'AnsibleScript'

    id = Column(Integer, ForeignKey('Script.id'), primary_key=True)
    playbook_path = Column(String)
    options = Column(MutableDict.as_mutable(PickleType), default={})

    __mapper_args__ = {
        'polymorphic_identity': 'ansible_playbook',
    }

    def __init__(self, playbook_path, **data):
        name = data['name'][0]
        super(AnsibleScript, self).__init__(name)
        self.playbook_path = playbook_path
        self.options = {}
        for key, value in data.items():
            if key in ansible_options:
                self.options[key] = value[0] if value else None

    def job(self, task):
        loader = DataLoader()
        hosts = [node.ip_address for node in task.nodes]
        temporary_file = NamedTemporaryFile(delete=False)
        temporary_file.write('\n'.join(hosts))
        temporary_file.close()

        # sources is a list of paths to inventory files"
        inventory = InventoryManager(loader=loader, sources=temporary_file.name)
        variable_manager = VariableManager(loader=loader, inventory=inventory)

        options_dict = {
            'listtags': False,
            'listtasks': False,
            'listhosts': False,
            'syntax': False,
            'connection': 'ssh',
            'module_path': None,
            'forks': 100,
            'remote_user': None,
            'private_key_file': None,
            'ssh_common_args': None,
            'ssh_extra_args': None,
            'sftp_extra_args': None,
            'scp_extra_args': None,
            'become': False,
            'become_method': None,
            'become_user': None,
            'verbosity': None,
            'check': False,
            'diff': False
        }

        Options = namedtuple('Options', list(options_dict))
        passwords = {}
        playbook_executor = PlaybookExecutor(
            playbooks=[self.playbook_path],
            inventory=inventory,
            variable_manager=variable_manager,
            loader=loader,
            options=Options(**options_dict),
            passwords=passwords
        )

        results = playbook_executor.run()
        return results


type_to_class = {
    'netmiko_config': NetmikoConfigScript,
    'napalm_config': NapalmConfigScript,
    'file_transfer': FileTransferScript,
    'napalm_getters': NapalmGettersScript,
    'ansible_playbook': AnsibleScript
}


def script_factory(**kwargs):
    cls = type_to_class[kwargs['type']]
    script = get_obj(cls, name=kwargs['name'])
    for property, value in kwargs.items():
        if property in script.__dict__:
            setattr(script, property, value)
    db.session.add(script)
    db.session.commit()
