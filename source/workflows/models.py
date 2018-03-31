from base.models import script_workflow_table, task_workflow_table, CustomBase
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship


class ScriptEdge(CustomBase):

    __tablename__ = 'ScriptEdge'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    source_id = Column(Integer, ForeignKey('Script.id'))
    source = relationship(
        'Script',
        primaryjoin="Script.id == ScriptEdge.source_id",
        backref='destinations'
    )
    destination_id = Column(Integer, ForeignKey('Script.id'))
    destination = relationship(
        'Script',
        primaryjoin="Script.id == ScriptEdge.destination_id"
    )
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
    type = Column(String)
    scripts = relationship(
        'Script',
        secondary=script_workflow_table,
        back_populates='workflows'
    )
    tasks = relationship(
        "Task",
        secondary=task_workflow_table,
        back_populates="workflows"
    )
    start_script_id = Column(Integer, ForeignKey('Script.id'))
    start_script = relationship(
        'Script',
        primaryjoin="Script.id == Workflow.start_script_id"
    )
    edges = relationship('ScriptEdge', back_populates='workflow')

    def __init__(self, **kwargs):
        self.name = kwargs['name']
        self.description = kwargs['description']

    def job(self, args):
        task, node, results = args
        layer, visited = {self.start_script}, set()
        print('test')
        while layer:
            new_layer = set()
            for script in layer:
                visited.add(script)
                for neighbor in script.script_neighbors(self):
                    if neighbor not in visited:
                        new_layer.add(neighbor)
                        results[script.name] = neighbor.name
            layer = new_layer
