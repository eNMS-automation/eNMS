from base.models import CustomBase
from .properties import *
from sqlalchemy import Column, ForeignKey, Integer, String, Float
from sqlalchemy.orm import relationship


class Object(CustomBase):
    
    __tablename__ = 'Object'

    id = Column(Integer, primary_key=True)
    name = Column(String(120))
    vendor = Column(String(120))
    type = Column(String(50))
    
    __mapper_args__ = {
        'polymorphic_identity':'Object',
        'polymorphic_on': type
    }
    
    properties = object_common_properties
    
    def __init__(self, **kwargs):
        for property, value in kwargs.items():
            if property in public_properties:
                # depending on whether value is an iterable or not, we must
                # unpack it's value (when **kwargs is request.form, some values
                # will be a 1-element list)
                if hasattr(value, '__iter__') and not isinstance(value, str):
                    value ,= value
                setattr(self, property, value)

    def __repr__(self):
        return str(self.name)

class Node(Object):
    
    __tablename__ = 'Node'
    
    id = Column(Integer, ForeignKey('Object.id'), primary_key=True)
    operating_system = Column(String(120))
    os_version = Column(String(120))
    ip_address = Column(String(120))
    longitude = Column(Float)
    latitude = Column(Float)
    
    __mapper_args__ = {
        'polymorphic_identity':'Node',
    }
    
    properties = node_common_properties
    class_type = 'node'
    
    def __init__(self, **kwargs):
        super(Node, self).__init__(**kwargs)
        
    @classmethod
    def get_properties(cls):
        return dict(
            list(
                # https://stackoverflow.com/questions/17575074
                super(Node).__get__(cls, None).properties.items())
                + list(cls.properties.items())
            )
        
    def napalm_connection(self, user, driver, transport):
        driver = get_network_driver(driver)
        node = driver(
                        hostname = self.ip_address, 
                        username = user.username,
                        password = user.password, 
                        optional_args = {
                                         'secret': user.secret, 
                                         'transport': transport
                                         }
                        )
        node.open()
        return node
        
class Antenna(Node):
    
    __tablename__ = 'Antenna'
    
    __mapper_args__ = {
        'polymorphic_identity': 'Antenna',
    }
    
    id = Column(Integer, ForeignKey('Node.id'), primary_key=True)
    
    def __init__(self, **kwargs):
        super(Antenna, self).__init__(**kwargs)

class Firewall(Node):
    
    __tablename__ = 'Firewall'
    
    __mapper_args__ = {
        'polymorphic_identity': 'Firewall',
    }
    
    id = Column(Integer, ForeignKey('Node.id'), primary_key=True)
    
    def __init__(self, **kwargs):
        super(Firewall, self).__init__(**kwargs)

class Host(Node):
    
    __tablename__ = 'Host'
    
    __mapper_args__ = {
        'polymorphic_identity': 'Host',
    }
    
    id = Column(Integer, ForeignKey('Node.id'), primary_key=True)
    
    def __init__(self, **kwargs):
        super(Host, self).__init__(**kwargs)

class OpticalSwitch(Node):
    
    __tablename__ = 'Optical switch'

    __mapper_args__ = {
        'polymorphic_identity': 'Optical switch',
    }
    
    id = Column(Integer, ForeignKey('Node.id'), primary_key=True)
    
    def __init__(self, **kwargs):
        super(OpticalSwitch, self).__init__(**kwargs)

class Regenerator(Node):
    
    __tablename__ = 'Regenerator'
    
    __mapper_args__ = {
        'polymorphic_identity': 'Regenerator',
    }
    
    id = Column(Integer, ForeignKey('Node.id'), primary_key=True)
    
    def __init__(self, **kwargs):
        super(Regenerator, self).__init__(**kwargs)

class Router(Node):
    
    __tablename__ = 'Router'
    
    __mapper_args__ = {
        'polymorphic_identity':'Router',
    }
    
    id = Column(Integer, ForeignKey('Node.id'), primary_key=True)
    
    def __init__(self, **kwargs):
        super(Router, self).__init__(**kwargs)

class Server(Node):
    
    __tablename__ = 'Server'
    
    __mapper_args__ = {
        'polymorphic_identity':'Server',
    }
    
    id = Column(Integer, ForeignKey('Node.id'), primary_key=True)
    
    def __init__(self, **kwargs):
        super(Server, self).__init__(**kwargs)

class Switch(Node):
    
    __tablename__ = 'Switch'
    
    __mapper_args__ = {
        'polymorphic_identity':'Switch',
    }
    
    id = Column(Integer, ForeignKey('Node.id'), primary_key=True)
    
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
        ForeignKey('Node.id'),
        primary_key=True
        )

    destination_id = Column(
        Integer,
        ForeignKey('Node.id'),
        primary_key=True
        )
        
    source = relationship(
        Node,
        primaryjoin = source_id == Node.id,
        backref = 'sources'
        )

    destination = relationship(
        Node,
        primaryjoin = destination_id == Node.id,
        backref = 'destinations'
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
        return dict(
            list(
                # https://stackoverflow.com/questions/17575074
                super(Link).__get__(cls, None).properties.items())
                + list(cls.properties.items())
            )

class BgpPeering(Link):
    
    __tablename__ = 'BGP peering'
    
    __mapper_args__ = {
        'polymorphic_identity': 'BGP peering',
    }
    
    id = Column(Integer, ForeignKey('Link.id'), primary_key=True)
    
    def __init__(self, **kwargs):
        super(BgpPeering, self).__init__(**kwargs)

class Etherchannel(Link):
    
    __tablename__ = 'Etherchannel'
    
    __mapper_args__ = {
        'polymorphic_identity': 'Etherchannel',
    }
    
    id = Column(Integer, ForeignKey('Link.id'), primary_key=True)
    
    def __init__(self, **kwargs):
        super(Etherchannel, self).__init__(**kwargs)

class EthernetLink(Link):
    
    __tablename__ = 'Ethernet link'
    
    __mapper_args__ = {
        'polymorphic_identity': 'Ethernet link',
    }
    
    id = Column(Integer, ForeignKey('Link.id'), primary_key=True)
    
    def __init__(self, **kwargs):
        super(EthernetLink, self).__init__(**kwargs)

class OpticalLink(Link):
    
    __tablename__ = 'Optical link'
    
    __mapper_args__ = {
        'polymorphic_identity': 'Optical link',
    }
    
    id = Column(Integer, ForeignKey('Link.id'), primary_key=True)
    
    def __init__(self, **kwargs):
        super(OpticalLink, self).__init__(**kwargs)

class OpticalChannel(Link):
    
    __tablename__ = 'Optical channel'
    
    __mapper_args__ = {
        'polymorphic_identity': 'Optical channel',
    }
    
    id = Column(Integer, ForeignKey('Link.id'), primary_key=True)
    
    def __init__(self, **kwargs):
        super(OpticalChannel, self).__init__(**kwargs)

class Pseudowire(Link):
    
    __tablename__ = 'Pseudowire'
    
    __mapper_args__ = {
        'polymorphic_identity': 'Pseudowire',
    }
    
    id = Column(Integer, ForeignKey('Link.id'), primary_key=True)
    
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
print(object_class)
