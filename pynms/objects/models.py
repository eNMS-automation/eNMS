from collections import OrderedDict
from sqlalchemy import Column, ForeignKey, Integer, String, Float
from sqlalchemy.orm import relationship
from base.models import CustomBase

class Object(CustomBase):
    
    id = Column(Integer, primary_key=True)
    name = Column(String(120))
    vendor = Column(String(120))
    type = Column(String(50))
    
    __mapper_args__ = {
        'polymorphic_identity':'Object',
        'polymorphic_on': type
    }
    
    properties = OrderedDict([
        ('name', 'Name'),
        ('type', 'Type'),
        ('vendor', 'Vendor')
        ])
    
    __tablename__ = 'Object'
    
    def __init__(self, **kwargs):
        for kw, value in kwargs.items():
            setattr(self, kw, value)

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
    
    properties = OrderedDict([
        ('operating_system', 'Operating System'),
        ('os_version', 'OS version'),
        ('ip_address', 'IP address'),
        ('longitude', 'Longitude'),
        ('latitude', 'Latitude')
        ])
    
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

    def __repr__(self):
        return str(self.name)
        
class Antenna(Node):
    
    __tablename__ = 'Antenna'
    
    __mapper_args__ = {
        'polymorphic_identity': 'Antenna',
    }
    
    id = Column(Integer, ForeignKey('Node.id'), primary_key=True)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class Firewall(Node):
    
    __tablename__ = 'Firewall'
    
    __mapper_args__ = {
        'polymorphic_identity': 'Firewall',
    }
    
    id = Column(Integer, ForeignKey('Node.id'), primary_key=True)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class Host(Node):
    
    __tablename__ = 'Host'
    
    __mapper_args__ = {
        'polymorphic_identity': 'Host',
    }
    
    id = Column(Integer, ForeignKey('Node.id'), primary_key=True)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class OpticalSwitch(Node):
    
    __tablename__ = 'OpticalSwitch'

    __mapper_args__ = {
        'polymorphic_identity': 'OpticalSwitch',
    }
    
    id = Column(Integer, ForeignKey('Node.id'), primary_key=True)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class Regenerator(Node):
    
    __tablename__ = 'Regenerator'
    
    __mapper_args__ = {
        'polymorphic_identity': 'Regenerator',
    }
    
    id = Column(Integer, ForeignKey('Node.id'), primary_key=True)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

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
        super().__init__(**kwargs)

class Switch(Node):
    
    __tablename__ = 'Switch'
    
    __mapper_args__ = {
        'polymorphic_identity':'Switch',
    }
    
    id = Column(Integer, ForeignKey('Node.id'), primary_key=True)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class Link(Object):
    
    __tablename__ = 'Link'

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
        
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @classmethod
    def get_properties(cls):
        return dict(
            list(
                # https://stackoverflow.com/questions/17575074
                super(Link).__get__(cls, None).properties.items())
                + list(cls.properties.items())
            )

class BgpPeering(Link):
    
    __tablename__ = 'BgpPeering'
    
    __mapper_args__ = {
        'polymorphic_identity':'BgpPeering',
    }
    
    id = Column(Integer, ForeignKey('Link.id'), primary_key=True)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class EtherChannel(Link):
    
    __tablename__ = 'EtherChannel'
    
    __mapper_args__ = {
        'polymorphic_identity':'EtherChannel',
    }
    
    id = Column(Integer, ForeignKey('Link.id'), primary_key=True)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class EthernetLink(Link):
    
    __tablename__ = 'EthernetLink'
    
    __mapper_args__ = {
        'polymorphic_identity':'EthernetLink',
    }
    
    id = Column(Integer, ForeignKey('Link.id'), primary_key=True)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class OpticalLink(Link):
    
    __tablename__ = 'OpticalLink'
    
    __mapper_args__ = {
        'polymorphic_identity':'OpticalLink',
    }
    
    id = Column(Integer, ForeignKey('Link.id'), primary_key=True)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class OpticalChannel(Link):
    
    __tablename__ = 'OpticalChannel'
    
    __mapper_args__ = {
        'polymorphic_identity':'OpticalChannel',
    }
    
    id = Column(Integer, ForeignKey('Link.id'), primary_key=True)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class PseudoWire(Link):
    
    __tablename__ = 'PseudoWire'
    
    __mapper_args__ = {
        'polymorphic_identity':'PseudoWire',
    }
    
    id = Column(Integer, ForeignKey('Link.id'), primary_key=True)
    
    def __init__(self, **kwargs):
        super(PseudoWire, self).__init__(**kwargs)
    
## Dispatchers

node_class = OrderedDict([
('antenna', Antenna),
('firewall', Firewall),
('host', Host),
('optical switch', OpticalSwitch),
('regenerator', Regenerator),
('router', Router),
('switch', Switch),
('server', Server),
])

link_class = OrderedDict([
('BGP peering', BgpPeering),
('etherchannel', EtherChannel),
('ethernet link', EthernetLink),
('optical channel', OpticalChannel),
('optical link', OpticalLink),
('pseudowire', PseudoWire)
])
