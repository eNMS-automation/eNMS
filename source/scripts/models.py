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
        'polymorphic_identity':'Script',
        'polymorphic_on': type
    }
    
    def __init__(self, name):
        self.name = name
        
    def __repr__(self):
        return str(self.name)

class ClassicScript(Script):
    
    __tablename__ = 'ClassicScript'

    id = Column(Integer, ForeignKey('Script.id'), primary_key=True)
    
    __mapper_args__ = {
        'polymorphic_identity':'ClassicScript',
    }
    
    def __init__(self, content, **data):
        name ,= data['name']
        super(ClassicScript, self).__init__(name)
        self.content = ''.join(content)
        
class AnsibleScript(Script):
    
    __tablename__ = 'AnsibleScript'
    
    id = Column(Integer, ForeignKey('Script.id'), primary_key=True)
    playbook_path = Column(String)
    options = Column(MutableDict.as_mutable(PickleType), default={})
    
    __mapper_args__ = {
        'polymorphic_identity':'AnsibleScript',
    }
    
    def __init__(self, playbook_path, **data):
        name ,= data['name']
        print(playbook_path)
        super(AnsibleScript, self).__init__(name)
        self.playbook_path = playbook_path
        self.options = {}
        for key, value in data.items():
            if key in ansible_options:
                self.options[key] ,= value if value else None
