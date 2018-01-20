from base.models import CustomBase
from sqlalchemy import Column, Integer, String

class Script(CustomBase):
    
    __tablename__ = 'Script'

    id = Column(Integer, primary_key=True)
    name = Column(String(120))
    type = Column(String(50))
    content = Column(String)
    
    def __init__(self, content, **data):
        self.name ,= data['name']
        self.type ,= data['type']
        self.content = ''.join(content)
        
    def __repr__(self):
        return str(self.name)
