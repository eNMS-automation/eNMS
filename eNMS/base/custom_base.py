from eNMS import db
from eNMS.base.properties import (
    boolean_properties,
    cls_to_properties,
    json_properties,
    list_properties
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
            # unchecked tickbox do not yield any value when posting a form,
            # and they yield 'y' if checked
            if property in boolean_properties:
                value = property in kwargs
            elif property in json_properties:
                str_dict, = kwargs[property]
                value = loads(str_dict) if str_dict else {}
            setattr(self, property, value)

    @property
    def properties(self):
        class_name = self.__tablename__
        return {p: getattr(self, p) for p in cls_to_properties[class_name]}

    @classmethod
    def choices(cls):
        return [(obj.id, obj.name) for obj in cls.query.all()]

    @classmethod
    def serialize(cls):
        return [obj.serialized for obj in cls.query.all()]


def base_factory(cls, **kwargs):
    instance = get_obj(cls, name=kwargs['name'])
    if instance:
        instance.update(**kwargs)
    else:
        instance = cls(**kwargs)
        db.session.add(instance)
    db.session.commit()
    return instance
