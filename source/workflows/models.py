from base.models import script_workflow_table, CustomBase
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship


class ScriptEdge(CustomBase):

    __tablename__ = 'ScriptEdge'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    source_id = Column(Integer, ForeignKey('Script.id'))
    source = relationship('Script', primaryjoin="Script.id == ScriptEdge.source_id")
    destination_id = Column(Integer, ForeignKey('Script.id'))
    destination = relationship('Script', primaryjoin="Script.id == ScriptEdge.destination_id")
    workflow_id = Column(Integer, ForeignKey('Workflow.id'))
    workflow = relationship('Workflow', back_populates='edges')

    def __init__(self, source, destination):
        self.source = source
        self.destination = destination
        self.name = '{} -> {}'.format(self.source.name, self.destination.name)


class Workflow(CustomBase):

    __tablename__ = 'Workflow'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    description = Column(String)
    scripts = relationship(
        'Script',
        secondary=script_workflow_table,
        back_populates='workflows'
    )
    edges = relationship('ScriptEdge', back_populates='workflow')

    def __init__(self, **kwargs):
        self.name = kwargs['name']
        self.description = kwargs['description']
