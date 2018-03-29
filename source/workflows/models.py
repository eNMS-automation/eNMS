from base.models import CustomBase
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship


class ScriptEdge(CustomBase):

    __tablename__ = 'ScriptEdge'

    source = Column(Integer, ForeignKey('Script.id'), primary_key=True)
    destination = Column(Integer, ForeignKey('Script.id'), primary_key=True)
    workflow = Column(Integer, ForeignKey('Workflow.id'))

    def __init__(self, source, destination):
        self.source = source
        self.destination = destination

class Workflow(CustomBase):

    __tablename__ = 'Workflow'

    id = Column(Integer, primary_key=True)
    name = Column(String(120))
    edges = relationship('ScriptEdge')
