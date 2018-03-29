from base.models import association_table, CustomBase
from collections import OrderedDict
from .properties import (
    link_common_properties,
    node_common_properties,
    object_common_properties
)
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Float
from sqlalchemy.orm import backref, relationship


def initialize_properties(function):
    def wrapper(self, **kwargs):
        function(self, **kwargs)
        for property, value in kwargs.items():
            # depending on whether value is an iterable or not, we must
            # unpack it's value (when **kwargs is request.form, some values
            # will be a 1-element list)
            if hasattr(value, '__iter__') and not isinstance(value, str):
                value = value[0]
            setattr(self, property, value)
    return wrapper


class Object(CustomBase):

    __tablename__ = 'Object'

    id = Column(Integer, primary_key=True)
    name = Column(String(120), unique=True)
    description = Column(String)
    location = Column(String)
    vendor = Column(String(120))
    type = Column(String(50))
    visible = Column(Boolean, default=True)

    __mapper_args__ = {
        'polymorphic_identity': 'Object',
        'polymorphic_on': type
    }

    properties = object_common_properties

    @initialize_properties
    def __init__(self, **kwargs):
        pass

    @classmethod
    def visible_choices(cls):
        return [(obj, obj) for obj in cls.visible_objects()]

    def __repr__(self):
        return self.name


class Node(Object):

    __tablename__ = 'Node'

    id = Column(Integer, ForeignKey('Object.id'), primary_key=True)
    operating_system = Column(String(120))
    os_version = Column(String(120))
    ip_address = Column(String(120))
    longitude = Column(Float)
    latitude = Column(Float)
    secret_password = Column(String)
    tasks = relationship(
        "Task",
        secondary=association_table,
        back_populates="nodes"
    )

    __mapper_args__ = {
        'polymorphic_identity': 'Node',
    }

    properties = node_common_properties
    class_type = 'node'

    @initialize_properties
    def __init__(self, **kwargs):
        super(Node, self).__init__(**kwargs)

    @classmethod
    def get_properties(cls):
        return super(Node).__get__(cls, None).properties + cls.properties


class Antenna(Node):

    __tablename__ = 'Antenna'

    __mapper_args__ = {
        'polymorphic_identity': 'Antenna',
    }

    id = Column(Integer, ForeignKey('Node.id'), primary_key=True)
    subtype = 'antenna'

    @initialize_properties
    def __init__(self, **kwargs):
        super(Antenna, self).__init__(**kwargs)


class Firewall(Node):

    __tablename__ = 'Firewall'

    __mapper_args__ = {
        'polymorphic_identity': 'Firewall',
    }

    id = Column(Integer, ForeignKey('Node.id'), primary_key=True)
    subtype = 'firewall'

    @initialize_properties
    def __init__(self, **kwargs):
        super(Firewall, self).__init__(**kwargs)


class Host(Node):

    __tablename__ = 'Host'

    __mapper_args__ = {
        'polymorphic_identity': 'Host',
    }

    id = Column(Integer, ForeignKey('Node.id'), primary_key=True)
    subtype = 'host'

    @initialize_properties
    def __init__(self, **kwargs):
        super(Host, self).__init__(**kwargs)


class OpticalSwitch(Node):

    __tablename__ = 'Optical switch'

    __mapper_args__ = {
        'polymorphic_identity': 'Optical switch',
    }

    id = Column(Integer, ForeignKey('Node.id'), primary_key=True)
    subtype = 'optical_switch'

    @initialize_properties
    def __init__(self, **kwargs):
        super(OpticalSwitch, self).__init__(**kwargs)


class Regenerator(Node):

    __tablename__ = 'Regenerator'

    __mapper_args__ = {
        'polymorphic_identity': 'Regenerator',
    }

    id = Column(Integer, ForeignKey('Node.id'), primary_key=True)
    subtype = 'regenerator'

    @initialize_properties
    def __init__(self, **kwargs):
        super(Regenerator, self).__init__(**kwargs)


class Router(Node):

    __tablename__ = 'Router'

    __mapper_args__ = {
        'polymorphic_identity': 'Router',
    }

    id = Column(Integer, ForeignKey('Node.id'), primary_key=True)
    subtype = 'router'

    @initialize_properties
    def __init__(self, **kwargs):
        super(Router, self).__init__(**kwargs)


class Server(Node):

    __tablename__ = 'Server'

    __mapper_args__ = {
        'polymorphic_identity': 'Server',
    }

    id = Column(Integer, ForeignKey('Node.id'), primary_key=True)
    subtype = 'server'

    @initialize_properties
    def __init__(self, **kwargs):
        super(Server, self).__init__(**kwargs)


class Switch(Node):

    __tablename__ = 'Switch'

    __mapper_args__ = {
        'polymorphic_identity': 'Switch',
    }

    id = Column(Integer, ForeignKey('Node.id'), primary_key=True)
    subtype = 'switch'

    @initialize_properties
    def __init__(self, **kwargs):
        super(Switch, self).__init__(**kwargs)


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
        backref=backref('source', cascade="all, delete-orphan")
    )

    destination = relationship(
        Node,
        primaryjoin=destination_id == Node.id,
        backref=backref('destination', cascade="all, delete-orphan")
    )

    properties = OrderedDict([
        ('source', 'Source'),
        ('destination', 'Destination')
    ])

    properties = link_common_properties
    class_type = 'link'

    def __init__(self, **kwargs):
        super(Link, self).__init__(**kwargs)

    @classmethod
    def get_properties(cls):
        return super(Link).__get__(cls, None).properties + cls.properties


class BgpPeering(Link):

    __tablename__ = 'BGP peering'

    __mapper_args__ = {
        'polymorphic_identity': 'BGP peering',
    }

    id = Column(Integer, ForeignKey('Link.id'), primary_key=True)
    subtype = 'bgp_peering'
    color = '#77ebca'

    def __init__(self, **kwargs):
        super(BgpPeering, self).__init__(**kwargs)


class Etherchannel(Link):

    __tablename__ = 'Etherchannel'

    __mapper_args__ = {
        'polymorphic_identity': 'Etherchannel',
    }

    id = Column(Integer, ForeignKey('Link.id'), primary_key=True)
    subtype = 'Etherchannel'
    color = '#cf228a'

    def __init__(self, **kwargs):
        super(Etherchannel, self).__init__(**kwargs)


class EthernetLink(Link):

    __tablename__ = 'Ethernet link'

    __mapper_args__ = {
        'polymorphic_identity': 'Ethernet link',
    }

    id = Column(Integer, ForeignKey('Link.id'), primary_key=True)
    subtype = 'ethernet_link'
    color = '#0000ff'

    def __init__(self, **kwargs):
        super(EthernetLink, self).__init__(**kwargs)


class OpticalLink(Link):

    __tablename__ = 'Optical link'

    __mapper_args__ = {
        'polymorphic_identity': 'Optical link',
    }

    id = Column(Integer, ForeignKey('Link.id'), primary_key=True)
    subtype = 'optical_link'
    color = '#d4222a'

    def __init__(self, **kwargs):
        super(OpticalLink, self).__init__(**kwargs)


class OpticalChannel(Link):

    __tablename__ = 'Optical channel'

    __mapper_args__ = {
        'polymorphic_identity': 'Optical channel',
    }

    id = Column(Integer, ForeignKey('Link.id'), primary_key=True)
    subtype = 'optical_channel'
    color = '#ff8247'

    def __init__(self, **kwargs):
        super(OpticalChannel, self).__init__(**kwargs)


class Pseudowire(Link):

    __tablename__ = 'Pseudowire'

    __mapper_args__ = {
        'polymorphic_identity': 'Pseudowire',
    }

    id = Column(Integer, ForeignKey('Link.id'), primary_key=True)
    subtype = 'Pseudowire'
    color = '#902bec'

    def __init__(self, **kwargs):
        super(Pseudowire, self).__init__(**kwargs)

## Dispatchers


node_class = OrderedDict([
    ('Antenna', Antenna),
    ('Firewall', Firewall),
    ('Host', Host),
    ('Optical switch', OpticalSwitch),
    ('Regenerator', Regenerator),
    ('Router', Router),
    ('Switch', Switch),
    ('Server', Server),
])

node_subtypes = (
    'antenna',
    'firewall',
    'host',
    'optical_switch',
    'regenerator',
    'router',
    'server',
    'switch'
)

link_class = OrderedDict([
    ('BGP peering', BgpPeering),
    ('Etherchannel', Etherchannel),
    ('Ethernet link', EthernetLink),
    ('Optical channel', OpticalChannel),
    ('Optical link', OpticalLink),
    ('Pseudowire', Pseudowire)
])

object_class = OrderedDict()
for cls_dict in (node_class, link_class):
    object_class.update(cls_dict)


def get_obj(db, model, **kwargs):
    return db.session.query(model).filter_by(**kwargs).first()


# todo if the type is not the same, delete the object and recreate it
def object_factory(db, **kwargs):
    obj_type = kwargs['type']
    cls = Node if obj_type in node_class else Link
    obj = get_obj(db, cls, name=kwargs['name'])
    if obj:
        for property, value in kwargs.items():
            if property in obj.__dict__:
                setattr(obj, property, value)
    elif obj_type in link_class:
        source = get_obj(db, Node, name=kwargs.pop('source'))
        destination = get_obj(db, Node, name=kwargs.pop('destination'))
        obj = link_class[obj_type](
            source_id=source.id,
            destination_id=destination.id,
            source=source,
            destination=destination,
            **kwargs
        )
    else:
        obj = object_class[obj_type](**kwargs)
    db.session.add(obj)
    db.session.commit()
