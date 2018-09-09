from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import backref, relationship

from eNMS.base.associations import task_workflow_table
from eNMS.base.models import CustomBase
from eNMS.scripts.models import Job


class WorkflowEdge(CustomBase):

    __tablename__ = 'WorkflowEdge'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    type = Column(Boolean)
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
    end_task = Column(Integer)

    default_properties = (
        'name',
        'description'
    )

    __mapper_args__ = {
        'polymorphic_identity': 'workflow',
    }

    @property
    def serialized(self):
        properties = self.properties
        properties['tasks'] = [obj.properties for obj in getattr(self, 'tasks')]
        properties['edges'] = [edge.serialized for edge in self.edges]
        return properties
