from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from time import sleep


from eNMS import db
from eNMS.base.helpers import get_obj
from eNMS.base.models import CustomBase
from eNMS.base.properties import cls_to_properties
from eNMS.tasks.models import Task


class WorkflowEdge(CustomBase):

    __tablename__ = 'WorkflowEdge'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    type = Column(String)
    source_id = Column(Integer, ForeignKey('InnerTask.id'))
    source = relationship(
        'InnerTask',
        primaryjoin='InnerTask.id == WorkflowEdge.source_id',
        backref='destinations'
    )
    destination_id = Column(Integer, ForeignKey('InnerTask.id'))
    destination = relationship(
        'InnerTask',
        primaryjoin='InnerTask.id == WorkflowEdge.destination_id'
    )
    workflow_id = Column(Integer, ForeignKey('Workflow.id'))
    workflow = relationship('Workflow', back_populates='edges')

    def __init__(self, type, source, destination):
        self.type = type
        self.source = source
        self.destination = destination
        self.name = '{} -> {}'.format(self.source.name, self.destination.name)

    @property
    def properties(self):
        return {p: str(getattr(self, p)) for p in cls_to_properties['WorkflowEdge']}

    @property
    def serialized(self):
        properties = self.properties
        properties['source'] = self.source.serialized
        properties['destination'] = self.destination.serialized
        return properties


class Workflow(CustomBase):

    __tablename__ = 'Workflow'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    description = Column(String)
    type = Column(String)
    vendor = Column(String)
    operating_system = Column(String)
    tasks = relationship('ScheduledWorkflowTask', back_populates='scheduled_workflow')
    inner_tasks = relationship('InnerTask', back_populates='parent_workflow')
    edges = relationship('WorkflowEdge', back_populates='workflow')
    start_task = Column(Integer)

    default_properties = (
        'name',
        'description',
        'type'
    )

    def __init__(self, **kwargs):
        for property in self.default_properties:
            setattr(self, property, kwargs[property])

    @property
    def properties(self):
        return {p: str(getattr(self, p)) for p in cls_to_properties['Workflow']}

    @property
    def serialized(self):
        properties = self.properties
        for prop in ('tasks', 'inner_tasks'):
            properties[prop] = [obj.properties for obj in getattr(self, prop)]
        properties['edges'] = [edge.serialized for edge in self.edges]
        return properties

    def run(self):
        layer, visited = set(), set()
        start_task = get_obj(Task, id=self.start_task)
        result = True
        if start_task:
            layer.add(start_task)
        while layer:
            new_layer = set()
            print(layer)
            for task in layer:
                print(task)
                visited.add(task)
                success = task.run()
                print(success)
                if not success:
                    result = False
                edge_type = 'success' if success else 'failure'
                for neighbor in task.task_neighbors(edge_type):
                    print(neighbor, neighbor not in visited)
                    if neighbor not in visited:
                        new_layer.add(neighbor)
                sleep(task.waiting_time)
            layer = new_layer
        return result


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
