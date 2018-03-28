from base.models import CustomBase
from .forms import ansible_options
from netmiko import ConnectHandler
from sqlalchemy import Column, ForeignKey, Integer, PickleType, String
from sqlalchemy.ext.mutable import MutableDict


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


class ConfigScript(Script):

    __tablename__ = 'ConfigScript'

    id = Column(Integer, ForeignKey('Script.id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': 'ConfigScript',
    }

    def __init__(self, content, **data):
        name = data['name'][0]
        super(ConfigScript, self).__init__(name)
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
