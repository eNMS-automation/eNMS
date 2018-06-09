from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from time import sleep


from eNMS import db
from eNMS.base.helpers import get_obj
from eNMS.base.models import CustomBase
from eNMS.base.properties import cls_to_properties


class WorkflowEdge(CustomBase):

    __tablename__ = 'WorkflowEdge'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    type = Column(String)
    source_id = Column(Integer, ForeignKey('Script.id'))
    source = relationship(
        'Script',
        primaryjoin="Script.id == WorkflowEdge.source_id",
        backref='destinations'
    )
    destination_id = Column(Integer, ForeignKey('Script.id'))
    destination = relationship(
        'Script',
        primaryjoin="Script.id == WorkflowEdge.destination_id"
    )
    workflow_id = Column(Integer, ForeignKey('Workflow.id'))
    workflow = relationship('Workflow', back_populates='edges')

    def __init__(self, type, source, destination):
        self.type = type
        self.source = source
        self.destination = destination
        self.name = '{} -> {}'.format(self.source.name, self.destination.name)

    @property
    def serialized(self):
        properties = {
            'name': self.name,
            'type': self.type,
            'source': self.source.serialized,
            'destination': self.destination.serialized
        }
        return properties

class Workflow(CustomBase):

    __tablename__ = 'Workflow'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    description = Column(String)
    type = Column(String)
    vendor = Column(String)
    operating_system = Column(String)
    tasks = relationship('Task', back_populates='workflow')
    edges = relationship('WorkflowEdge', back_populates='workflow')

    properties = (
        'name',
        'description',
        'type'
    )

    def __init__(self, **kwargs):
        for property in self.properties:
            setattr(self, property, kwargs[property])

    @property
    def serialized(self):
        properties = {p: str(getattr(self, p)) for p in cls_to_properties['Workflow']}
        properties['tasks'] = [task.serialized for task in self.tasks]
        properties['edges'] = [edge.serialized for edge in self.edges]
        return properties

    def job(self, args):
        task, node, results = args
        while layer:
            new_layer = set()
            for script in layer:
                visited.add(script)
                script_results = {}
                success = script.job([task, node, script_results])
                edge_type = 'success' if success else 'failure'
                results[script.name] = script_results
                for neighbor in script.script_neighbors(self, edge_type):
                    if neighbor not in visited:
                        new_layer.add(neighbor)
                sleep(script.waiting_time)
            layer = new_layer


def workflow_factory(**kwargs):
    workflow = get_obj(Workflow, name=kwargs['name'])
    if workflow:
        for property, value in kwargs.items():
            if property in workflow.__dict__:
                setattr(workflow, property, value)
    else:
        workflow = Workflow(**kwargs)
    db.session.add(workflow)
    db.session.commit()
    return workflow
