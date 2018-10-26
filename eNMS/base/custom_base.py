from json import dumps, loads

from eNMS import db
from eNMS.base.helpers import fetch
from eNMS.base.properties import (
    cls_to_properties,
    property_types,
    boolean_properties
)


class CustomBase(db.Model):

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
                value = kwargs[property] in ('y', 'on')
            elif 'regex' in property:
                value = property in kwargs
            elif property_type == dict:
                value = loads(value) if value else {}
            elif property_type in [float, int]:
                value = property_type(value or 0)
            print(property, value)
            setattr(self, property, value)

    @property
    def properties(self):
        class_name, result = self.__tablename__, {}
        print(class_name, cls_to_properties[class_name])
        for property in cls_to_properties[class_name]:
            try:
                dumps(getattr(self, property))
                result[property] = getattr(self, property)
            except TypeError:
                result[property] = str(getattr(self, property))
        return result

    @property
    def serialized(self):
        return self.properties

    @property
    def visible(self):
        return not (hasattr(self, 'hidden') and self.hidden)

    @classmethod
    def choices(cls):
        return [(obj.id, obj.name) for obj in cls.query.all() if obj.visible]

    @classmethod
    def serialize(cls):
        return [obj.serialized for obj in cls.query.all() if obj.visible]


def factory(cls, **kwargs):
    if 'id' in kwargs:
        instance = fetch(cls, id=kwargs.pop('id'))
    else:
        instance = fetch(cls, name=kwargs['name'])
    if instance:
        instance.update(**kwargs)
    else:
        instance = cls(**kwargs)
        db.session.add(instance)
    db.session.commit()
    return instance
