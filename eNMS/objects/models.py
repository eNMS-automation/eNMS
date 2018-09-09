from re import search
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Float
from sqlalchemy.orm import backref, relationship

from eNMS.base.associations import (
    pool_device_table,
    pool_link_table,
    task_device_table,
    task_pool_table
)
from eNMS.base.custom_base import CustomBase
from eNMS.base.properties import (
    link_public_properties,
    device_public_properties
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


class Device(Object):

    __tablename__ = 'Device'

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
        secondary=task_device_table,
        back_populates='devices'
    )
    pools = relationship(
        'Pool',
        secondary=pool_device_table,
        back_populates='devices'
    )

    class_type = 'device'

    __mapper_args__ = {
        'polymorphic_identity': 'Device',
    }


class Link(Object):

    __tablename__ = 'Link'

    __mapper_args__ = {
        'polymorphic_identity': 'Link',
    }

    id = Column(Integer, ForeignKey('Object.id'), primary_key=True)
    source_id = Column(
        Integer,
        ForeignKey('Device.id')
    )
    destination_id = Column(
        Integer,
        ForeignKey('Device.id')
    )
    source = relationship(
        Device,
        primaryjoin=source_id == Device.id,
        backref=backref('source', cascade='all, delete-orphan')
    )
    destination = relationship(
        Device,
        primaryjoin=destination_id == Device.id,
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


class Pool(CustomBase):

    __tablename__ = 'Pool'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    description = Column(String)
    devices = relationship(
        'Device',
        secondary=pool_device_table,
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
    device_name = Column(String)
    device_name_regex = Column(Boolean)
    device_description = Column(String)
    device_description_regex = Column(Boolean)
    device_model = Column(String)
    device_model_regex = Column(Boolean)
    device_location = Column(String)
    device_location_regex = Column(Boolean)
    device_type = Column(String)
    device_type_regex = Column(Boolean)
    device_vendor = Column(String)
    device_vendor_regex = Column(Boolean)
    device_operating_system = Column(String)
    device_operating_system_regex = Column(Boolean)
    device_os_version = Column(String)
    device_os_version_regex = Column(Boolean)
    device_ip_address = Column(String)
    device_ip_address_regex = Column(Boolean)
    device_longitude = Column(String)
    device_longitude_regex = Column(Boolean)
    device_latitude = Column(String)
    device_latitude_regex = Column(Boolean)
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
        for prop in ('devices', 'links'):
            properties[prop] = [obj.properties for obj in getattr(self, prop)]
        return properties

    def compute_pool(self):
        self.devices = list(filter(self.object_match, Device.query.all()))
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
        for p in device_public_properties:
            for property in f'device_{p} device_{p}_regex'.split():
                result[property] = getattr(self, property)
        result['name'], result['description'] = self.name, self.description
        return result

    def object_match(self, obj):
        return all(
            # if the device-regex property is not in the request, the
            # regex box is unticked and we only check that the values
            # are equal.
            str(value) == getattr(self, obj.class_type + '_' + prop)
            if not getattr(self, f'{obj.class_type}_{prop}_regex')
            # if it is ticked, we use re.search to check that the value
            # of the device property matches the regular expression.
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
            'devices': [device.serialized for device in self.devices],
            'links': [link.serialized for link in self.links]
        }
