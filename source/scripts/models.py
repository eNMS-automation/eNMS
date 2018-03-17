from base.models import CustomBase
from .forms import ansible_options
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


class FileTransferScript(Script):

    __tablename__ = 'FileTransferScript'

    id = Column(Integer, ForeignKey('Script.id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': 'FileTransferScript',
    }

    def __init__(self, content, **data):
        name = data['name'][0]
        super(FileTransferScript, self).__init__(name)


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
