from json import loads

from eNMS import db
from eNMS.base.helpers import retrieve
from eNMS.base.properties import cls_to_properties, property_types


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
            if property_type == bool or 'regex' in property:
                value = property in kwargs
            elif property_type == dict:
                value = loads(value) if value else {}
            elif property_type in [float, int]:
                value = property_type(value or 0)
            setattr(self, property, value)

    @property
    def properties(self):
        class_name = self.__tablename__
        return {p: str(getattr(self, p)) for p in cls_to_properties[class_name]}

    @property
    def serialized(self):
        return self.properties

    @classmethod
    def choices(cls):
        return [(obj.id, obj.name) for obj in cls.query.all()]

    @classmethod
    def serialize(cls):
        return [obj.serialized for obj in cls.query.all()]


def factory(cls, **kwargs):
    instance = retrieve(cls, name=kwargs['name'])
    if instance:
        instance.update(**kwargs)
    else:
        instance = cls(**kwargs)
        db.session.add(instance)
    db.session.commit()
    return instance
