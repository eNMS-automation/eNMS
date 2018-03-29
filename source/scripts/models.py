from base.models import CustomBase
from .forms import ansible_options
from netmiko import ConnectHandler
from sqlalchemy import Column, ForeignKey, Integer, PickleType, String
from sqlalchemy.ext.mutable import MutableDict
from napalm import get_network_driver
try:
    from ansible.parsing.dataloader import DataLoader
    from ansible.vars.manager import VariableManager
    from ansible.inventory.manager import InventoryManager
    from ansible.executor.playbook_executor import PlaybookExecutor
except Exception:
    import warnings
    warnings.warn('ansible import failed: ansible feature deactivated')


class Script(CustomBase):

    __tablename__ = 'Script'

    id = Column(Integer, primary_key=True)
    name = Column(String(120))
    type = Column(String(50))
    content = Column(String)

    __mapper_args__ = {
        'polymorphic_identity': 'Script',
        'polymorphic_on': type
    }

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return str(self.name)


class NetmikoConfigScript(Script):

    __tablename__ = 'NetmikoConfigScript'

    id = Column(Integer, ForeignKey('Script.id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': 'NetmikoConfigScript',
    }

    def __init__(self, content, **data):
        name = data['name'][0]
        super(NetmikoConfigScript, self).__init__(name)
        self.content = ''.join(content)

    def job(self, kwargs):
        results = kwargs.pop('results')
        name = kwargs.pop('name')
        script_type = kwargs.pop('type')
        try:
            netmiko_handler = ConnectHandler(**kwargs)
            if script_type == 'configuration':
                netmiko_handler.send_config_set(self.content.splitlines())
                result = 'configuration OK'
            else: 
                # script_type is 'show_commands':
                outputs = []
                for show_command in self.content.splitlines():
                    outputs.append(netmiko_handler.send_command(show_command))
                result = '\n\n'.join(outputs)
            netmiko_handler.disconnect()
        except Exception as e:
            result = 'netmiko config did not work because of {}'.format(e)
        results[name] = result


class FileTransferScript(Script):

    __tablename__ = 'FileTransferScript'

    id = Column(Integer, ForeignKey('Script.id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': 'FileTransferScript',
    }

    def __init__(self, **data):
        name = data['name'][0]
        self.source_file = data['source_file'][0]
        self.destination_file = data['destination_file'][0]
        self.file_system = data['file_system'][0]
        self.direction = data['direction'][0]
        super(FileTransferScript, self).__init__(name)

    def job(self, kwargs):
        results = kwargs.pop('results')
        name = kwargs.pop('name')
        script_type = kwargs.pop('type')
        try:
            netmiko_handler = ConnectHandler(**kwargs)
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
        results[name] = result


class NapalmConfigScript(Script):

    __tablename__ = 'NapalmConfigScript'

    id = Column(Integer, ForeignKey('Script.id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': 'NapalmConfigScript',
    }

    def __init__(self, content, **data):
        name = data['name'][0]
        super(NapalmConfigScript, self).__init__(name)
        self.content = ''.join(content)

    def job(self, kwargs):
        try:
            driver = get_network_driver(kwargs['driver'])
            napalm_driver = driver(
                hostname=kwargs['ip_address'],
                username=kwargs['username'],
                password=kwargs['password'],
                optional_args={'secret': kwargs['secret']}
            )
            napalm_driver.open()
            if kwargs['action'] in ('load_merge_candidate', 'load_replace_candidate'):
                getattr(napalm_driver, kwargs['action'])(config=kwargs['script'])
            else:
                getattr(napalm_driver, kwargs['action'])()
            napalm_driver.close()
        except Exception as e:
            result = 'napalm config did not work because of {}'.format(e)
        else:
            result = 'configuration OK'
        kwargs['results'][kwargs['name']] = result


class NapalmGettersScript(Script):

    __tablename__ = 'NapalmGettersScript'

    id = Column(Integer, ForeignKey('Script.id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': 'NapalmGettersScript',
    }

    def __init__(self, content, **data):
        name = data['name'][0]
        super(ConfigScript, self).__init__(name)
        self.content = ''.join(content)

    def job(self, kwargs):
        try:
            driver = get_network_driver(kwargs['driver'])
            napalm_driver = driver(
                hostname=kwargs['ip_address'],
                username=kwargs['username'],
                password=kwargs['password'],
                optional_args={'secret': kwargs['secret']}
            )
            napalm_driver.open()
            for getter in kwargs['getters']:
                try:
                    result = str_dict(getattr(napalm_driver, getter)())
                except Exception as e:
                    result = '{} could not be retrieve because of {}'.format(getter, e)
            napalm_driver.close()
        except Exception as e:
            result = 'getters process did not work because of {}'.format(e)
        kwargs['results'][kwargs['name']] = result


class AnsibleScript(Script):

    __tablename__ = 'AnsibleScript'

    id = Column(Integer, ForeignKey('Script.id'), primary_key=True)
    playbook_path = Column(String)
    options = Column(MutableDict.as_mutable(PickleType), default={})

    __mapper_args__ = {
        'polymorphic_identity': 'AnsibleScript',
    }

    def __init__(self, playbook_path, **data):
        name = data['name'][0]
        super(AnsibleScript, self).__init__(name)
        self.playbook_path = playbook_path
        self.options = {}
        for key, value in data.items():
            if key in ansible_options:
                self.options[key] = value[0] if value else None

    def job(self, nodes_info):
        loader = DataLoader()
        hosts = [info[1] for info in nodes_info]
        temporary_file = NamedTemporaryFile(delete=False)
        temporary_file.write('\n'.join(hosts))
        temporary_file.close()
    
        # sources is a list of paths to inventory files"
        inventory = InventoryManager(loader=loader, sources=temporary_file.name)
        variable_manager = VariableManager(loader=loader, inventory=inventory)
        playbook_path = script.playbook_path
    
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
            playbooks=[playbook_path],
            inventory=inventory,
            variable_manager=variable_manager,
            loader=loader,
            options=Options(**options_dict),
            passwords=passwords
        )
    
        results = playbook_executor.run()