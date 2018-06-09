from sqlalchemy import Column, ForeignKey, Integer, String, Table


from eNMS import db
from eNMS.base.properties import cls_to_properties


class CustomBase(db.Model):

    __abstract__ = True

    # simplifies the syntax for flask forms
    @classmethod
    def choices(cls):
        return [(obj.id, obj.name) for obj in cls.query.all()]

    def __repr__(self):
        return self.name

    def __lt__(self, other):
        return True

    @property
    def serialized(self):
        return {p: getattr(self, p) for p in cls_to_properties[self.__tablename__]}

    @classmethod
    def serialize(cls):
        return [obj.serialized for obj in cls.query.all()]

class Log(CustomBase):

    __tablename__ = 'Log'

    id = Column(Integer, primary_key=True)
    source = Column(String)
    content = Column(String)

    def __init__(self, source, content):
        self.source = source
        self.content = content

    def __repr__(self):
        return self.content


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

pool_node_table = Table(
    'pool_node_association',
    CustomBase.metadata,
    Column('pool_id', Integer, ForeignKey('Pool.id')),
    Column('node_id', Integer, ForeignKey('Node.id'))
)

pool_link_table = Table(
    'pool_link_association',
    CustomBase.metadata,
    Column('pool_id', Integer, ForeignKey('Pool.id')),
    Column('link_id', Integer, ForeignKey('Link.id'))
)
