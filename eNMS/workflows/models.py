from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import backref, relationship

from eNMS import db
from eNMS.base.associations import task_workflow_table
from eNMS.base.helpers import get_obj
from eNMS.base.models import CustomBase
from eNMS.base.properties import cls_to_properties
from eNMS.scripts.models import Job


class WorkflowEdge(CustomBase):

    __tablename__ = 'WorkflowEdge'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    type = Column(String)
    source_id = Column(Integer, ForeignKey('Task.id'))
    source = relationship(
        'Task',
        primaryjoin='Task.id == WorkflowEdge.source_id',
        backref=backref('destinations', cascade='all, delete-orphan')
    )
    destination_id = Column(Integer, ForeignKey('Task.id'))
    destination = relationship(
        'Task',
        primaryjoin='Task.id == WorkflowEdge.destination_id',
        backref=backref('sources', cascade='all, delete-orphan')
    )
    workflow_id = Column(Integer, ForeignKey('Workflow.id'))
    workflow = relationship('Workflow', back_populates='edges')

    def __init__(self, type, source, destination):
        self.type = type
        self.source = source
        self.destination = destination
        self.name = f'{self.source.name} -> {self.destination.name}'

    @property
    def properties(self):
        return {p: getattr(self, p) for p in cls_to_properties['WorkflowEdge']}

    @property
    def serialized(self):
        properties = self.properties
        properties['source'] = self.source.serialized
        properties['destination'] = self.destination.serialized
        return properties


class Workflow(Job):

    __tablename__ = 'Workflow'

    id = Column(Integer, ForeignKey('Job.id'), primary_key=True)
    vendor = Column(String)
    operating_system = Column(String)
    tasks = relationship(
        'Task',
        secondary=task_workflow_table,
        back_populates='workflows'
    )
    task = relationship('WorkflowTask', back_populates='workflow')
    edges = relationship('WorkflowEdge', back_populates='workflow')
    start_task = Column(Integer)

    default_properties = (
        'name',
        'description'
    )

    __mapper_args__ = {
        'polymorphic_identity': 'workflow',
    }

    def __init__(self, **kwargs):
        for property in self.default_properties:
            setattr(self, property, kwargs[property])

    @property
    def properties(self):
        return {p: getattr(self, p) for p in cls_to_properties['Workflow']}

    @property
    def serialized(self):
        properties = self.properties
        properties['tasks'] = [obj.properties for obj in getattr(self, 'tasks')]
        properties['edges'] = [edge.serialized for edge in self.edges]
        return properties


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
