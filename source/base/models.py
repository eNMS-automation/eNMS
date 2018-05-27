from .database import Base
from sqlalchemy import Column, ForeignKey, Integer, String, Table


class CustomBase(Base):

    __abstract__ = True

    # simplifies the syntax for flask forms
    @classmethod
    def choices(cls):
        return [(obj, obj) for obj in cls.query.all()]

    def __repr__(self):
        return self.name

    # the visible classmethod is here because it can apply to both objects and logs
    @classmethod
    def visible_objects(cls):
        return (obj for obj in cls.query.all() if obj.visible)


class Log(CustomBase):

    __tablename__ = 'Log'

    id = Column(Integer, primary_key=True)
    source = Column(String)
    content = Column(String)

    properties = (
        'source',
        'content'
    )

    def __init__(self, source, content):
        self.source = source
        self.content = content

    def __repr__(self):
        return self.content

    def get_properties(self):
        return [getattr(self, property) for property in self.properties]


task_node_table = Table(
    'task_node_association',
    CustomBase.metadata,
    Column('node_id', Integer, ForeignKey('Node.id')),
    Column('task_id', Integer, ForeignKey('Task.id'))
)

task_script_table = Table(
    'task_script_association',
    CustomBase.metadata,
    Column('script_id', Integer, ForeignKey('Script.id')),
    Column('task_id', Integer, ForeignKey('Task.id'))
)

task_workflow_table = Table(
    'task_workflow_association',
    CustomBase.metadata,
    Column('workflow_id', Integer, ForeignKey('Workflow.id')),
    Column('task_id', Integer, ForeignKey('Task.id'))
)

script_workflow_table = Table(
    'script_workflow_association',
    CustomBase.metadata,
    Column('script_id', Integer, ForeignKey('Script.id')),
    Column('workflow_id', Integer, ForeignKey('Workflow.id'))
)

filter_node_table = Table(
    'filter_node_association',
    CustomBase.metadata,
    Column('filter_id', Integer, ForeignKey('Filter.id')),
    Column('node_id', Integer, ForeignKey('Node.id'))
)

filter_link_table = Table(
    'filter_link_association',
    CustomBase.metadata,
    Column('filter_id', Integer, ForeignKey('Filter.id')),
    Column('link_id', Integer, ForeignKey('Link.id'))
)
