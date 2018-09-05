from collections import OrderedDict
from re import search
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Float
from sqlalchemy.orm import backref, relationship

from eNMS import db
from eNMS.base.associations import (
    pool_node_table,
    pool_link_table,
    task_node_table,
    task_pool_table
)
from eNMS.base.custom_base import base_factory, CustomBase
from eNMS.base.helpers import retrieve, integrity_rollback
from eNMS.base.properties import (
    cls_to_properties,
    link_public_properties,
    node_common_properties,
    node_public_properties,
    object_common_properties
)


class Object(CustomBase):

    __tablename__ = 'Object'

    id = Column(Integer, primary_key=True)
    name = Column(String(120), unique=True)
    subtype = Column(String)
    description = Column(String)
    model = Column(String)
    location = Column(String)
    vendor = Column(String(120))
    type = Column(String(50))
    visible = Column(Boolean, default=True)

    __mapper_args__ = {
        'polymorphic_identity': 'Object',
        'polymorphic_on': type
    }


class Node(Object):

    __tablename__ = 'Node'

    id = Column(Integer, ForeignKey('Object.id'), primary_key=True)
    operating_system = Column(String(120))
    os_version = Column(String(120))
    ip_address = Column(String(120))
    longitude = Column(Float)
    latitude = Column(Float)
    username = Column(String)
    password = Column(String)
    secret_password = Column(String)
    tasks = relationship(
        'ScriptTask',
        secondary=task_node_table,
        back_populates='nodes'
    )
    pools = relationship(
        'Pool',
        secondary=pool_node_table,
        back_populates='nodes'
    )

    class_type = 'node'

    __mapper_args__ = {
        'polymorphic_identity': 'Node',
    }

    @property
    def serialized(self):
        properties = self.properties
        for prop in ('tasks', 'pools'):
            properties[prop] = [obj.properties for obj in getattr(self, prop)]
        return properties


class Link(Object):

    __tablename__ = 'Link'

    __mapper_args__ = {
        'polymorphic_identity': 'Link',
    }

    id = Column(Integer, ForeignKey('Object.id'), primary_key=True)
    source_id = Column(
        Integer,
        ForeignKey('Node.id')
    )
    destination_id = Column(
        Integer,
        ForeignKey('Node.id')
    )
    source = relationship(
        Node,
        primaryjoin=source_id == Node.id,
        backref=backref('source', cascade='all, delete-orphan')
    )
    destination = relationship(
        Node,
        primaryjoin=destination_id == Node.id,
        backref=backref('destination', cascade='all, delete-orphan')
    )
    pools = relationship(
        'Pool',
        secondary=pool_link_table,
        back_populates='links'
    )

    class_type = 'link'

    @property
    def serialized(self):
        properties = {k: str(v) for k, v in self.properties.items()}
        for prop in ('source', 'destination'):
            properties[prop + '_properties'] = getattr(self, prop).serialized
        return properties


def object_factory(**kwargs):
    obj_type = kwargs['type']
    cls = Node if obj_type in node_class else Link
    obj = retrieve(cls, name=kwargs['name'])
    if obj:
        obj.update(**kwargs)
    elif obj_type in link_class:
        if 'import' in kwargs:
            source = retrieve(Node, name=kwargs.pop('source'))
            destination = retrieve(Node, name=kwargs.pop('destination'))
        else:
            source = retrieve(Node, id=kwargs.pop('source'))
            destination = retrieve(Node, id=kwargs.pop('destination'))
        obj = Link(
            source_id=source.id,
            destination_id=destination.id,
            source=source,
            destination=destination,
            **kwargs
        )
        db.session.add(obj)
    else:
        obj = Node(**kwargs)
        db.session.add(obj)
    db.session.commit()
    return obj


class Pool(CustomBase):

    __tablename__ = 'Pool'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    description = Column(String)
    nodes = relationship(
        'Node',
        secondary=pool_node_table,
        back_populates='pools'
    )
    links = relationship(
        'Link',
        secondary=pool_link_table,
        back_populates='pools'
    )
    tasks = relationship(
        'ScriptTask',
        secondary=task_pool_table,
        back_populates='pools'
    )
    node_name = Column(String)
    node_name_regex = Column(Boolean)
    node_description = Column(String)
    node_description_regex = Column(Boolean)
    node_model = Column(String)
    node_model_regex = Column(Boolean)
    node_location = Column(String)
    node_location_regex = Column(Boolean)
    node_type = Column(String)
    node_type_regex = Column(Boolean)
    node_vendor = Column(String)
    node_vendor_regex = Column(Boolean)
    node_operating_system = Column(String)
    node_operating_system_regex = Column(Boolean)
    node_os_version = Column(String)
    node_os_version_regex = Column(Boolean)
    node_ip_address = Column(String)
    node_ip_address_regex = Column(Boolean)
    node_longitude = Column(String)
    node_longitude_regex = Column(Boolean)
    node_latitude = Column(String)
    node_latitude_regex = Column(Boolean)
    link_name = Column(String)
    link_name_regex = Column(Boolean)
    link_description = Column(String)
    link_description_regex = Column(Boolean)
    link_model = Column(String)
    link_model_regex = Column(Boolean)
    link_location = Column(String)
    link_location_regex = Column(Boolean)
    link_type = Column(String)
    link_type_regex = Column(Boolean)
    link_vendor = Column(String)
    link_vendor_regex = Column(Boolean)
    link_source = Column(String)
    link_source_regex = Column(Boolean)
    link_destination = Column(String)
    link_destination_regex = Column(Boolean)

    def update(self, **kwargs):
        super().update(**kwargs)
        self.compute_pool()

    @property
    def serialized(self):
        properties = self.properties
        for prop in ('nodes', 'links'):
            properties[prop] = [obj.properties for obj in getattr(self, prop)]
        return properties

    def compute_pool(self):
        self.nodes = list(filter(self.object_match, Node.query.all()))
        self.links = []
        for link in Link.query.all():
            # source and destination do not belong to a link __dict__, because
            # they are SQLalchemy relationships and not columns
            # we update __dict__ with these properties for the filtering
            # system to include them
            link.__dict__.update({
                'source': link.source,
                'destination': link.destination
            })
            if self.object_match(link):
                self.links.append(link)

    def get_properties(self):
        result = {}
        for p in link_public_properties:
            for property in f'link_{p} link_{p}_regex'.split():
                result[property] = getattr(self, property)
        for p in node_public_properties:
            for property in f'node_{p} node_{p}_regex'.split():
                result[property] = getattr(self, property)
        result['name'], result['description'] = self.name, self.description
        return result

    def object_match(self, obj):
        return all(
            # if the node-regex property is not in the request, the
            # regex box is unticked and we only check that the values
            # are equal.
            str(value) == getattr(self, obj.class_type + '_' + prop)
            if not getattr(self, f'{obj.class_type}_{prop}_regex')
            # if it is ticked, we use re.search to check that the value
            # of the node property matches the regular expression.
            else search(getattr(self, obj.class_type + '_' + prop), str(value))
            for prop, value in obj.__dict__.items()
            # we consider only the properties in the form
            if f'{obj.class_type}_{prop}' in self.__dict__ and
            # providing that the property field in the form is not empty
            # (empty field <==> property ignored)
            getattr(self, obj.class_type + '_' + prop)
        )

    def filter_objects(self):
        return {
            'nodes': [node.serialized for node in self.nodes],
            'links': [link.serialized for link in self.links]
        }


default_pools = (
    {'name': 'All objects'},
    {'name': 'Nodes only', 'link_name': '^$', 'link_name_regex': True},
    {'name': 'Links only', 'node_name': '^$', 'node_name_regex': True}
)


@integrity_rollback
def create_default_pools():
    for pool in default_pools:
        pool = base_factory(Pool, **pool)
