from json import dumps, loads

from eNMS import db
from eNMS.base.properties import (
    cls_to_properties,
    property_types,
    boolean_properties,
    serialization_properties
)


class Base(db.Model):

    __abstract__ = True

    def __init__(self, **kwargs):
        self.update(**kwargs)

    def __lt__(self, other):
        return True

    def __repr__(self):
        return self.name

    def update(self, **kwargs):
        for property, value in kwargs.items():
            property_type = property_types.get(property, None)
            if property in boolean_properties:
                value = kwargs[property] in ('y', 'on', 'false', 'true', True)
            elif 'regex' in property:
                value = property in kwargs
            elif property_type == dict:
                value = loads(value) if value else {}
            elif property_type in [float, int]:
                value = property_type(value or 0)
            setattr(self, property, value)

    @property
    def properties(self):
        class_name, result = self.__tablename__, {}
        for property in cls_to_properties[class_name]:
            try:
                dumps(getattr(self, property))
                result[property] = getattr(self, property)
            except TypeError:
                result[property] = str(getattr(self, property))
        return result

    def to_dict(self, export=False):
        get = 'id' if export else 'properties'
        properties = self.properties
        for property in serialization_properties:
            if hasattr(self, property):
                if hasattr(getattr(self, property), 'properties'):
                    properties[property] = getattr(getattr(self, property), get)
            if hasattr(self, f'{property}s'):
                # a workflow has edges: we need to know not only the edge
                # properties, but also the properties of its source and
                # destination: we need the serialized edge.
                properties[f'{property}s'] = [
                    getattr(obj, get) for obj in getattr(self, f'{property}s')
                ]
        return properties

    @property
    def serialized(self):
        return self.to_dict()

    @property
    def visible(self):
        return not (hasattr(self, 'hidden') and self.hidden)

    @classmethod
    def export(cls):
        return [obj.to_dict(export=True) for obj in cls.query.all()]

    @classmethod
    def choices(cls):
        return [(obj.id, obj.name) for obj in cls.query.all() if obj.visible]

    @classmethod
    def serialize(cls):
        return [obj.serialized for obj in cls.query.all() if obj.visible]


classes, service_classes = {}, {}
